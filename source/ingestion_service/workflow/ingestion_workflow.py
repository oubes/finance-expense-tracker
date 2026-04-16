# ---- Imports ----
from typing import TypedDict
import logging

from pydantic import ValidationError

from langgraph.graph import StateGraph, START, END
from src.shared.graph_builder import GraphSaver
from src.core.schemas.workflow.ingestion_schema import WorkflowOutput
from src.core.schemas.pipeline.ingestion_schema import PipelineOutput

logger = logging.getLogger(__name__)


# ---- State ----
class IngestionState(TypedDict):
    raw_output: list[object] | None
    normalized_output: list[dict] | None
    validated_output: list[WorkflowOutput] | None
    table_empty: bool | None
    overwrite: bool

    source_documents: list[object] | None
    chunked_documents: list[dict] | None
    filtered_chunks: list[dict] | None
    validated_summaries: list[dict] | None
    embeddings: list[dict] | None
    final_pipeline_output: list[PipelineOutput] | None


# ---- Workflow ----
class IngestionWorkflow:

    def __init__(
        self,
        pdf_loader,
        chunker,
        llm_service,
        embedding_service,
        db_client,
        init_table_fn,
        upsert_fn,
        delete_fn,
        count_fn,
        doc_name: str,
        score_threshold: float,
    ) -> None:

        self.pdf_loader = pdf_loader
        self.chunker = chunker
        self.llm_service = llm_service
        self.embedding_service = embedding_service

        self.db_client = db_client
        self.init_table_fn = init_table_fn
        self.upsert_fn = upsert_fn
        self.delete_fn = delete_fn
        self.count_fn = count_fn

        self.doc_name = doc_name
        self.score_threshold = score_threshold

        self.required_keys = {"title", "summary", "flag"}
        self.allowed_flags = {"SUCCESS_FLAG"}

        self.graph = StateGraph(IngestionState)
        self._build_graph()
        self.graph_saver = GraphSaver("ingestion_workflow.png")

    # ---- Graph ----
    def _build_graph(self) -> None:

        self.graph.add_node("init_table", self.init_table_node)
        self.graph.add_node("check_empty", self.check_empty_node)

        self.graph.add_node("pdf_loader", self.pdf_loader_node)
        self.graph.add_node("chunker", self.chunker_node)
        self.graph.add_node("filter_score", self.filter_score_node)
        self.graph.add_node("metadata_cleanup", self.metadata_cleanup_node)
        self.graph.add_node("summary_generator", self.summary_generator_node)
        self.graph.add_node("embedding", self.embedding_node)
        self.graph.add_node("final_aggregation", self.final_aggregation_node)

        self.graph.add_node("normalize_output", self.normalize_output_node)
        self.graph.add_node("validate_output", self.validate_output_node)
        self.graph.add_node("upsert_output", self.upsert_output_node)

        self.graph.add_node("delete_data", self.delete_data_node)
        self.graph.add_node("decide_overwrite", self.decide_overwrite_node)

        self.graph.add_edge(START, "init_table")
        self.graph.add_edge("init_table", "check_empty")

        self.graph.add_conditional_edges(
            "check_empty",
            self.route_empty,
            {
                "empty": "pdf_loader",
                "not_empty": "decide_overwrite",
            },
        )

        self.graph.add_conditional_edges(
            "decide_overwrite",
            self.route_overwrite,
            {
                "true": "delete_data",
                "false": END,
            },
        )

        self.graph.add_edge("delete_data", "pdf_loader")

        self.graph.add_edge("pdf_loader", "chunker")
        self.graph.add_edge("chunker", "filter_score")
        self.graph.add_edge("filter_score", "metadata_cleanup")
        self.graph.add_edge("metadata_cleanup", "summary_generator")
        self.graph.add_edge("summary_generator", "embedding")
        self.graph.add_edge("embedding", "final_aggregation")

        self.graph.add_edge("final_aggregation", "normalize_output")
        self.graph.add_edge("normalize_output", "validate_output")
        self.graph.add_edge("validate_output", "upsert_output")
        self.graph.add_edge("upsert_output", END)

        self.compiled = self.graph.compile()

    # ---- Routing ----
    def route_empty(self, state: IngestionState) -> str:
        return "empty" if state.get("table_empty") else "not_empty"

    def route_overwrite(self, state: IngestionState) -> str:
        return "true" if state.get("overwrite") else "false"

    # ---- Init ----
    async def init_table_node(self, state: IngestionState) -> IngestionState:
        await self.init_table_fn()
        return state

    async def check_empty_node(self, state: IngestionState) -> IngestionState:
        count = await self.count_fn()
        state["table_empty"] = count == 0
        return state

    async def delete_data_node(self, state: IngestionState) -> IngestionState:
        logger.info("Deleting existing data (overwrite=True)")
        await self.delete_fn()
        return state

    # ---- Core Nodes ----

    def pdf_loader_node(self, state: IngestionState) -> IngestionState:
        try:
            state["source_documents"] = self.pdf_loader.load(self.doc_name)
        except Exception:
            logger.exception("[error] pdf_loader failed")
            state["source_documents"] = []
        return state

    def chunker_node(self, state: IngestionState) -> IngestionState:
        try:
            if not state["source_documents"]:
                return state

            chunks = self.chunker.chunk_documents(state["source_documents"], self.doc_name)

            for c in chunks:
                c["chunk_id"] = str(__import__("uuid").uuid4())
                metadata = c.get("metadata") or {}
                c["chunk_title"] = metadata.get("title") or f"chunk_{c['chunk_id']}"

            state["chunked_documents"] = chunks
            state["filtered_chunks"] = chunks

        except Exception:
            logger.exception("[error] chunker failed")

        return state

    def filter_score_node(self, state: IngestionState) -> IngestionState:
        try:
            state["filtered_chunks"] = [
                c for c in (state.get("filtered_chunks") or [])
                if (
                    not c["metadata"].get("is_toc", False)
                    and float(c.get("score", 0.0)) >= self.score_threshold
                )
            ]
        except Exception:
            logger.exception("[error] filter_score failed")
        return state

    def metadata_cleanup_node(self, state: IngestionState) -> IngestionState:
        try:
            state["filtered_chunks"] = [
                {**c, "metadata": dict(c.get("metadata", {}))}
                for c in (state.get("filtered_chunks") or [])
            ]
        except Exception:
            logger.exception("[error] metadata_cleanup failed")
        return state

    async def summary_generator_node(self, state: IngestionState) -> IngestionState:
        try:
            chunks = state.get("filtered_chunks") or []

            inputs = [
                {
                    "chunk_id": c["chunk_id"],
                    "title": c["chunk_title"],
                    "content": c["content"],
                }
                for c in chunks
            ]

            tasks = [
                self.llm_service.generate(
                    prompt=inp["content"]
                )
                for inp in inputs
            ]

            results = await __import__("asyncio").gather(*tasks, return_exceptions=True)

            state["validated_summaries"] = [
                {
                    "chunk_id": inputs[i]["chunk_id"],
                    "data": r["data"],
                    "state": True,
                }
                for i, r in enumerate(results)
                if not isinstance(r, Exception) and r.get("status") == "up"
            ]

        except Exception:
            logger.exception("[error] summary_generator failed")

        return state

    async def embedding_node(self, state: IngestionState) -> IngestionState:
        try:
            summaries = state.get("validated_summaries") or []

            texts = [s["data"] for s in summaries]
            result = await self.embedding_service.embed(texts)

            vectors = result.get("data") or []

            state["embeddings"] = [
                {
                    "chunk_id": summaries[i]["chunk_id"],
                    "vector": vectors[i],
                }
                for i in range(len(vectors))
            ]

        except Exception:
            logger.exception("[error] embedding failed")

        return state

    def final_aggregation_node(self, state: IngestionState) -> IngestionState:
        try:
            summaries = state.get("validated_summaries") or []
            embeddings = state.get("embeddings") or []
            chunks = state.get("filtered_chunks") or []

            summary_map = {s["chunk_id"]: s["data"] for s in summaries}
            embedding_map = {e["chunk_id"]: e["vector"] for e in embeddings}
            chunk_map = {c["chunk_id"]: c for c in chunks}

            records = []

            for cid, summary in summary_map.items():
                chunk = chunk_map.get(cid) or {}
                metadata = chunk.get("metadata") or {}

                records.append(
                    PipelineOutput(
                        id=__import__("uuid").uuid4(),
                        chunk_id=__import__("uuid").UUID(cid),
                        content=chunk.get("content", ""),
                        summary=summary,
                        score=float(chunk.get("score", 0.0)),
                        chunk_title=chunk.get("chunk_title", ""),
                        doc_title=self.doc_name,
                        source=metadata.get("source", ""),
                        page=metadata.get("page"),
                        total_pages=metadata.get("total_pages"),
                        embedding=embedding_map.get(cid, []),
                        created_at=__import__("datetime").datetime.now(
                            __import__("datetime").timezone.utc
                        ),
                        pipeline_version="1.0",
                    )
                )

            state["final_pipeline_output"] = records
            state["raw_output"] = records

        except Exception:
            logger.exception("[error] final_aggregation failed")

        return state

    # ---- Post ----

    async def normalize_output_node(self, state: IngestionState) -> IngestionState:
        raw = state.get("raw_output") or []
        state["normalized_output"] = [ # type: ignore
            item.model_dump() if hasattr(item, "model_dump") else item # type: ignore
            for item in raw
        ]
        return state

    async def validate_output_node(self, state: IngestionState) -> IngestionState:
        validated = []

        for item in (state.get("normalized_output") or []):
            try:
                validated.append(
                    WorkflowOutput(**PipelineOutput.model_validate(item).model_dump())
                )
            except ValidationError as ve:
                logger.error(f"[ValidationError] {ve}")

        state["validated_output"] = validated
        return state

    async def upsert_output_node(self, state: IngestionState) -> IngestionState:
        records = state.get("validated_output") or []

        if records:
            await self.upsert_fn(records=records)

        return state

    async def decide_overwrite_node(self, state: IngestionState) -> IngestionState:
        return state

    # ---- Runner ----
    async def run(self, overwrite: bool = True) -> IngestionState:

        initial_state: IngestionState = {
            "raw_output": None,
            "normalized_output": None,
            "validated_output": None,
            "table_empty": None,
            "overwrite": overwrite,
            "source_documents": None,
            "chunked_documents": None,
            "filtered_chunks": None,
            "validated_summaries": None,
            "embeddings": None,
            "final_pipeline_output": None,
        }

        self.graph_saver.save(self.compiled)
        return await self.compiled.ainvoke(initial_state) # type: ignore