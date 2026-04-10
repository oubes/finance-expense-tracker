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

PIPELINE_VERSION = "1.0"


# ---- State Definition ----
class IngestionState(TypedDict):
    source_documents: list[Document] | None
    chunked_documents: list[dict] | None
    filtered_chunks: list[dict] | None

    validated_summaries: list[dict] | None
    embeddings: list[dict] | None
    final_pipeline_output: list[PipelineOutput] | None


# ---- Utility ----
def attach_chunk_ids(chunks: list[dict]) -> list[dict]:
    logger.info(f"[step] attach_chunk_ids started | count={len(chunks)}")
    for c in chunks:
        c["chunk_id"] = str(uuid.uuid4())
    logger.info("[step] attach_chunk_ids completed")
    return chunks


# ---- Pipeline Class ----
class IngestionPipeline:

    # ---- Constructor ----
    def __init__(
        self,
        config: Any,
        pdf_loader: Any,
        chunker: Any,
        embedding: Any,
        safe_generator: Any,
    ) -> None:

        self.config = config
        self.pdf_loader = pdf_loader
        self.chunker = chunker
        self.embedding = embedding
        self.safe_generator = safe_generator

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

        # ---- merged node ----
        self.graph.add_node("filter_score", self.filter_score_node)

        self.graph.add_node("metadata_cleanup", self.metadata_cleanup_node)
        self.graph.add_node("summary_generator", self.summary_generator_node)

        self.graph.add_node("embedding", self.embedding_node)
        self.graph.add_node("final_aggregation", self.final_aggregation_node)

        self.graph.add_edge(START, "pdf_loader")
        self.graph.add_edge("pdf_loader", "chunker")
        self.graph.add_edge("chunker", "filter_score")

        self.graph.add_edge("filter_score", "metadata_cleanup")
        self.graph.add_edge("metadata_cleanup", "summary_generator")

        self.graph.add_edge("summary_generator", "embedding")
        self.graph.add_edge("embedding", "final_aggregation")
        self.graph.add_edge("final_aggregation", END)

        self.compiled = self.graph.compile()
        self.graph_saver = GraphSaver(filename="ingestion_pipeline.png")

    # ---- Logger Helper ----
    def _log_state(self, name: str, state: IngestionState) -> None:
        logger.info(
            f"[{name}] snapshot | "
            f"docs={len(state['source_documents'] or [])} | "
            f"chunks={len(state['chunked_documents'] or [])} | "
            f"filtered={len(state['filtered_chunks'] or [])} | "
            f"summaries={len(state['validated_summaries'] or [])} | "
            f"embeddings={len(state['embeddings'] or [])}"
        )

    # ---- Nodes ----

    # ---- PDF Loader ----
    def pdf_loader_node(self, state: IngestionState) -> IngestionState:
        try:
            state["source_documents"] = self.pdf_loader.load(self.doc_name)
        except Exception:
            logger.exception("[error] pdf_loader failed")
            state["source_documents"] = []
        self._log_state("pdf_loader", state)
        return state

    # ---- Chunker ----
    def chunker_node(self, state: IngestionState) -> IngestionState:
        try:
            if not state["source_documents"]:
                return state

            chunks = self.chunker.chunk_documents(state["source_documents"], self.doc_name)
            chunks = attach_chunk_ids(chunks)

            for c in chunks:
                metadata = c.get("metadata") or {}
                c["chunk_title"] = metadata.get("title") or f"chunk_{c['chunk_id']}"

            state["chunked_documents"] = chunks
            state["filtered_chunks"] = chunks

        except Exception:
            logger.exception("[error] chunker failed")

        self._log_state("chunker", state)
        return state

    # ---- Filter Score (TOC + Score) ----
    def filter_score_node(self, state: IngestionState) -> IngestionState:
        try:
            if not state["filtered_chunks"]:
                return state

            state["filtered_chunks"] = [
                c for c in state["filtered_chunks"]
                if (
                    not c["metadata"].get("is_toc", False)
                    and float(c.get("score", 0.0)) >= self.score_threshold
                )
            ]

        except Exception:
            logger.exception("[error] filter_score failed")

        self._log_state("filter_score", state)
        return state

    # ---- Metadata Cleanup ----
    def metadata_cleanup_node(self, state: IngestionState) -> IngestionState:
        try:
            if not state["filtered_chunks"]:
                return state

            state["filtered_chunks"] = [
                {**c, "metadata": dict(c.get("metadata", {}))}
                for c in state["filtered_chunks"]
            ]
        except Exception:
            logger.exception("[error] metadata_cleanup failed")

        self._log_state("metadata_cleanup", state)
        return state

    # ---- Summary Generator ----
    async def summary_generator_node(self, state: IngestionState) -> IngestionState:
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

            tasks = [
                self.safe_generator.run(
                    prompt_file_name="chunk_summarizer",
                    required_keys=self.required_keys,
                    allowed_flags=self.allowed_flags,
                    **inp,
                )
                for inp in inputs
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            state["validated_summaries"] = [
                {
                    "chunk_id": inputs[i]["chunk_id"],
                    "data": r["data"],  # type: ignore
                    "state": True
                }
                for i, r in enumerate(results)
                if not isinstance(r, Exception) and r.get("state")  # type: ignore
            ]

        except Exception:
            logger.exception("[error] summary_generator failed")

        self._log_state("summary_generator", state)
        return state

    # ---- Embedding ----
    async def embedding_node(self, state: IngestionState) -> IngestionState:
        try:
            if not state["validated_summaries"]:
                return state

            texts = [s["data"]["summary"] for s in state["validated_summaries"]]
            vectors = await self.embedding.embed_batch(texts)

            state["embeddings"] = [
                {
                    "chunk_id": state["validated_summaries"][i]["chunk_id"],
                    "vector": vectors[i]
                }
                for i in range(len(vectors))
            ]

        except Exception:
            logger.exception("[error] embedding failed")

        self._log_state("embedding", state)
        return state

    # ---- Final Aggregation ----
    def final_aggregation_node(self, state: IngestionState) -> IngestionState:
        try:
            summaries = state.get("validated_summaries")
            if not summaries:
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

                score = float(chunk.get("score", 0.0)) if chunk else 0.0

                records.append(
                    PipelineOutput(
                        id=uuid.uuid4(),
                        chunk_id=uuid.UUID(cid),
                        content=chunk.get("content", "") if chunk else "",
                        summary=summary.get("summary", ""),
                        score=score,
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

        except Exception:
            logger.exception("[error] final_aggregation failed")

        self._log_state("final_aggregation", state)
        return state

    # ---- Runner ----
    async def run(self) -> IngestionState:
        initial_state: IngestionState = {
            "source_documents": None,
            "chunked_documents": None,
            "filtered_chunks": None,
            "validated_summaries": None,
            "embeddings": None,
            "final_pipeline_output": None,
        }

        try:
            self.graph_saver.save(self.compiled)
            result = await self.compiled.ainvoke(initial_state)  # type: ignore
            self._log_state("pipeline_run", result)  # type: ignore
            return result  # type: ignore
        except Exception:
            logger.exception("[pipeline_run] failed")
            return initial_state