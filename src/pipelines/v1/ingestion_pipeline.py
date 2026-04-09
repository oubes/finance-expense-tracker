# ---- Imports ----
from typing import TypedDict, Any
import logging
import uuid
import asyncio
from datetime import datetime, timezone

from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END

from src.core.schemas.pipeline.ingestion_schema import PipelineOutput
from src.shared.graph_builder import GraphSaver


# ---- Logger ----
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

PIPELINE_VERSION = "1.0"


# ---- State Definition ----
class IngestionState(TypedDict):
    source_documents: list[Document] | None
    chunked_documents: list[dict] | None
    filtered_chunks: list[dict] | None

    summarization_messages: list[dict] | None
    generated_summaries_raw: list[dict] | None
    extracted_summaries_json: list[dict] | None
    validated_summaries: list[dict] | None
    collected_summaries: list[dict] | None

    embeddings: list[dict] | None
    final_pipeline_output: list[PipelineOutput] | None


# ---- Utility ----
def attach_chunk_ids(chunks: list[dict]) -> list[dict]:
    logger.info(f"[step] attach_chunk_ids started | count={len(chunks)}")
    try:
        for c in chunks:
            c["chunk_id"] = str(uuid.uuid4())
        logger.info(f"[step] attach_chunk_ids completed")
        return chunks
    except Exception as e:
        logger.exception(f"[error] attach_chunk_ids failed")
        raise e


# ---- Pipeline Class ----
class IngestionPipeline:

    def __init__(
        self,
        config: Any,
        pdf_loader: Any,
        chunker: Any,
        embedding: Any,
        llm_generator: Any,
        msg_builder: Any,
        json_extractor: Any,
        json_validator: Any
    ) -> None:

        self.config = config
        self.pdf_loader = pdf_loader
        self.chunker = chunker
        self.embedding = embedding
        self.llm_generator = llm_generator
        self.msg_builder = msg_builder
        self.json_extractor = json_extractor
        self.json_validator = json_validator

        self.doc_name = config.ingestion.doc_name
        self.score_threshold = config.ingestion.score_filter_threshold

        self.required_keys = {"title", "summary", "flag"}
        self.allowed_flags = {"SUCCESS_FLAG"}

        self.graph = StateGraph(IngestionState)
        self._build_graph()

    # ---- Graph Builder ----
    def _build_graph(self) -> None:
        self.graph.add_node("pdf_loader", self.pdf_loader_node)
        self.graph.add_node("chunker", self.chunker_node)
        self.graph.add_node("toc_filter", self.toc_filter_node)
        self.graph.add_node("score_filter", self.score_filter_node)
        self.graph.add_node("metadata_cleanup", self.metadata_cleanup_node)

        self.graph.add_node("msg_builder", self.summarization_msg_builder_node)
        self.graph.add_node("generate", self.summarization_generate_node)
        self.graph.add_node("extract", self.summarization_extract_node)
        self.graph.add_node("validate", self.summarization_validate_node)
        self.graph.add_node("collect", self.summarization_collect_node)

        self.graph.add_node("embedding", self.embedding_node)
        self.graph.add_node("final_aggregation", self.final_aggregation_node)

        self.graph.add_edge(START, "pdf_loader")
        self.graph.add_edge("pdf_loader", "chunker")
        self.graph.add_edge("chunker", "toc_filter")
        self.graph.add_edge("toc_filter", "score_filter")
        self.graph.add_edge("score_filter", "metadata_cleanup")
        self.graph.add_edge("metadata_cleanup", "msg_builder")
        self.graph.add_edge("msg_builder", "generate")
        self.graph.add_edge("generate", "extract")
        self.graph.add_edge("extract", "validate")
        self.graph.add_edge("validate", "collect")
        self.graph.add_edge("collect", "embedding")
        self.graph.add_edge("embedding", "final_aggregation")
        self.graph.add_edge("final_aggregation", END)

        self.compiled = self.graph.compile()
        self.graph_saver = GraphSaver(filename="ingestion_pipeline.png")

    # ---- Helpers ----
    def _log_state(self, name: str, state: IngestionState) -> None:
        logger.info(
            f"[{name}] snapshot counts | "
            f"docs={len(state['source_documents'] or [])} | "
            f"chunks={len(state['chunked_documents'] or [])} | "
            f"filtered={len(state['filtered_chunks'] or [])} | "
            f"messages={len(state['summarization_messages'] or [])} | "
            f"generated={len(state['generated_summaries_raw'] or [])} | "
            f"extracted={len(state['extracted_summaries_json'] or [])} | "
            f"validated={len(state['validated_summaries'] or [])} | "
            f"collected={len(state['collected_summaries'] or [])} | "
            f"embeddings={len(state['embeddings'] or [])}"
        )

    # ---- Nodes ----

    def pdf_loader_node(self, state: IngestionState) -> IngestionState:
        logger.info("[step] pdf_loader start")
        try:
            state["source_documents"] = self.pdf_loader.load(self.doc_name)
            logger.info("[step] pdf_loader done")
        except Exception:
            logger.exception("[error] pdf_loader failed")
            state["source_documents"] = []
        self._log_state("pdf_loader", state)
        return state

    def chunker_node(self, state: IngestionState) -> IngestionState:
        logger.info("[step] chunker start")
        try:
            if not state["source_documents"]:
                logger.warning("[step] chunker skipped (no docs)")
                return state

            chunks = self.chunker.chunk_documents(state["source_documents"], self.doc_name)
            chunks = attach_chunk_ids(chunks)

            for c in chunks:
                metadata = c.get("metadata") or {}
                c["chunk_title"] = metadata.get("title") or f"chunk_{c['chunk_id']}"

            state["chunked_documents"] = chunks
            state["filtered_chunks"] = chunks

            logger.info("[step] chunker done")
        except Exception:
            logger.exception("[error] chunker failed")
        self._log_state("chunker", state)
        return state

    def toc_filter_node(self, state: IngestionState) -> IngestionState:
        logger.info("[step] toc_filter start")
        try:
            if not state["filtered_chunks"]:
                return state

            before = len(state["filtered_chunks"])

            state["filtered_chunks"] = [
                c for c in state["filtered_chunks"]
                if not c["metadata"].get("is_toc", False)
            ]

            after = len(state["filtered_chunks"])
            logger.info("[step] toc_filter done")
        except Exception:
            logger.exception("[error] toc_filter failed")
        self._log_state("toc_filter", state)
        return state

    def score_filter_node(self, state: IngestionState) -> IngestionState:
        logger.info("[step] score_filter start")
        try:
            if not state["filtered_chunks"]:
                return state

            before = len(state["filtered_chunks"])

            state["filtered_chunks"] = [
                c for c in state["filtered_chunks"]
                if float(c.get("score", 0.0)) >= self.score_threshold
            ]

            after = len(state["filtered_chunks"])
            logger.info("[step] score_filter done")
        except Exception:
            logger.exception("[error] score_filter failed")
        self._log_state("score_filter", state)
        return state

    def metadata_cleanup_node(self, state: IngestionState) -> IngestionState:
        logger.info("[step] metadata_cleanup start")
        try:
            if not state["filtered_chunks"]:
                return state

            state["filtered_chunks"] = [
                {**c, "metadata": dict(c.get("metadata", {}))}
                for c in state["filtered_chunks"]
            ]
            logger.info("[step] metadata_cleanup done")
        except Exception:
            logger.exception("[error] metadata_cleanup failed")
        self._log_state("metadata_cleanup", state)
        return state

    # ---- Summarization ----
    async def summarization_msg_builder_node(self, state: IngestionState) -> IngestionState:
        logger.info("[step] msg_builder start")
        try:
            if not state["filtered_chunks"]:
                return state

            inputs = [
                {
                    "chunk_id": c["chunk_id"],
                    "title": c["chunk_title"],
                    "content": c["content"],
                }
                for c in state["filtered_chunks"]
            ]

            results = await self.msg_builder.build_batch_async(
                prompt_file_name="summarizer",
                inputs=inputs
            )

            messages = []
            for res, c in zip(results, state["filtered_chunks"]):
                res["chunk_id"] = c["chunk_id"]
                messages.append(res)

            state["summarization_messages"] = messages
            logger.info("[step] msg_builder done")
        except Exception:
            logger.exception("[error] msg_builder failed")

        self._log_state("msg_builder", state)
        return state

    async def summarization_generate_node(self, state: IngestionState) -> IngestionState:
        logger.info("[step] generate start")
        try:
            if not state["summarization_messages"]:
                return state

            tasks = [
                self.llm_generator.generate(msg["data"])
                for msg in state["summarization_messages"]
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            processed = []
            for i, r in enumerate(results):
                if isinstance(r, Exception):
                    continue
                processed.append({
                    "chunk_id": state["summarization_messages"][i]["chunk_id"],
                    "data": r
                })

            state["generated_summaries_raw"] = processed
            logger.info("[step] generate done")
        except Exception:
            logger.exception("[error] generate failed")

        self._log_state("generate", state)
        return state

    async def summarization_extract_node(self, state: IngestionState) -> IngestionState:
        logger.info("[step] extract start")
        try:
            if not state["generated_summaries_raw"]:
                return state

            extracted = await self.json_extractor.extract_batch(
                [r["data"] for r in state["generated_summaries_raw"]]
            )

            state["extracted_summaries_json"] = [
                {
                    "chunk_id": state["generated_summaries_raw"][i]["chunk_id"],
                    "data": extracted[i]
                }
                for i in range(len(extracted))
            ]

            logger.info("[step] extract done")
        except Exception:
            logger.exception("[error] extract failed")

        self._log_state("extract", state)
        return state

    def summarization_validate_node(self, state: IngestionState) -> IngestionState:
        logger.info("[step] validate start")
        try:
            if not state["extracted_summaries_json"]:
                return state

            validated = self.json_validator.validate_batch(
                [e["data"] for e in state["extracted_summaries_json"]],
                required_keys=self.required_keys,
                allowed_flags=self.allowed_flags
            )

            state["validated_summaries"] = [
                {
                    "chunk_id": state["extracted_summaries_json"][i]["chunk_id"],
                    "data": validated[i]["data"],
                    "state": validated[i]["state"]
                }
                for i in range(len(validated))
            ]

            logger.info("[step] validate done")
        except Exception:
            logger.exception("[error] validate failed")

        return state

    def summarization_collect_node(self, state: IngestionState) -> IngestionState:
        logger.info("[step] collect start")
        try:
            if not state["validated_summaries"]:
                return state

            state["collected_summaries"] = [
                v for v in state["validated_summaries"] if v["state"]
            ]

            logger.info("[step] collect done")
        except Exception:
            logger.exception("[error] collect failed")

        self._log_state("collect", state)
        return state

    # ---- Embedding ----
    async def embedding_node(self, state: IngestionState) -> IngestionState:
        logger.info("[step] embedding start")
        try:
            if not state["collected_summaries"]:
                return state

            texts = [s["data"]["summary"] for s in state["collected_summaries"]]
            vectors = await self.embedding.embed_batch(texts)

            state["embeddings"] = [
                {
                    "chunk_id": state["collected_summaries"][i]["chunk_id"],
                    "vector": vectors[i]
                }
                for i in range(len(vectors))
            ]

            logger.info("[step] embedding done")
        except Exception:
            logger.exception("[error] embedding failed")

        self._log_state("embedding", state)
        return state

    # ---- Final Aggregation ----
    def final_aggregation_node(self, state: IngestionState) -> IngestionState:
        logger.info("[step] final_aggregation start")
        try:
            summaries = state.get("collected_summaries")
            if not summaries:
                logger.warning("[step] final_aggregation skipped (no summaries)")
                return state

            embeddings = state.get("embeddings") or []
            chunks = state.get("filtered_chunks") or []

            summary_map = {s["chunk_id"]: s["data"] for s in summaries}
            embedding_map = {e["chunk_id"]: e["vector"] for e in embeddings}
            chunk_map = {c["chunk_id"]: c for c in chunks}

            records: list[PipelineOutput] = []

            for cid, summary in summary_map.items():
                chunk = chunk_map.get(cid)
                metadata = (chunk or {}).get("metadata") or {}

                raw_score = (
                    chunk.get("score")
                    if chunk and "score" in chunk
                    else metadata.get("score", 0.0)
                )

                try:
                    score_value = float(raw_score or 0.0)
                except (TypeError, ValueError):
                    score_value = 0.0

                records.append(
                    PipelineOutput(
                        id=uuid.uuid4(),
                        chunk_id=uuid.UUID(cid),
                        content=chunk.get("content", "") if chunk else "",
                        summary=summary.get("summary", ""),
                        score=score_value,
                        chunk_title=summary.get("title", ""),
                        doc_title=self.doc_name,
                        source=metadata.get("source", ""),
                        page=metadata.get("page"),
                        total_pages=metadata.get("total_pages"),
                        embedding=embedding_map.get(cid, []),
                        created_at=datetime.now(timezone.utc),
                        pipeline_version=PIPELINE_VERSION
                    )
                )

            state["final_pipeline_output"] = records
            logger.info("[step] final_aggregation done")
        except Exception:
            logger.exception("[error] final_aggregation failed")

        self._log_state("final_aggregation", state)
        return state

    # ---- Runner ----
    async def run(self) -> IngestionState:
        logger.info("[pipeline_run] start")

        initial_state: IngestionState = {
            "source_documents": None,
            "chunked_documents": None,
            "filtered_chunks": None,
            "summarization_messages": None,
            "generated_summaries_raw": None,
            "extracted_summaries_json": None,
            "validated_summaries": None,
            "collected_summaries": None,
            "embeddings": None,
            "final_pipeline_output": None,
        }

        try:
            self.graph_saver.save(self.compiled)
            result = await self.compiled.ainvoke(initial_state)  # type: ignore
            logger.info("[pipeline_run] completed")
            self._log_state("pipeline_run", result)  # type: ignore
            return result  # type: ignore
        except Exception:
            logger.exception("[pipeline_run] failed")
            return initial_state