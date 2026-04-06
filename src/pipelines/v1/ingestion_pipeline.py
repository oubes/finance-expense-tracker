# ---- Imports ----
from typing import TypedDict, Any
import logging
import uuid

from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END

from pipelines.v1.schemas.ingestion_schema import PipelineOutput, PipelineMeta

# ---- Logger ----
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---- Pipeline Version ----
PIPELINE_VERSION = "1.0"


# ---- State Definition ----
class IngestionState(TypedDict):
    document: list[Document] | None
    chunks: list[dict] | None
    filtered_chunks: list[dict] | None

    messages: list[dict] | None
    raw_summaries: list[dict] | None
    extracted: list[dict] | None
    validated: list[dict] | None

    embeddings: list[dict] | None
    summary: list[dict] | None


# ---- Utility ----
def attach_chunk_ids(chunks: list[dict]) -> list[dict]:
    logger.debug("Attaching chunk IDs")
    for c in chunks:
        c["chunk_id"] = str(uuid.uuid4())
    return chunks


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

        # ---- Dependencies ----
        self.pdf_loader = pdf_loader
        self.chunker = chunker
        self.embedding = embedding
        self.llm_generator = llm_generator
        self.msg_builder = msg_builder
        self.json_extractor = json_extractor
        self.json_validator = json_validator

        # ---- Config extraction ----
        self.doc_name = config.ingestion.doc_name
        self.score_threshold = config.ingestion.score_filter_threshold

        # ---- Validation config (inline) ----
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

        self.graph.add_node("msg_builder", self.summarizer_msg_builder_node)
        self.graph.add_node("generate", self.summarizer_generate_node)
        self.graph.add_node("extract", self.summarizer_extract_node)
        self.graph.add_node("validate", self.summarizer_validate_node)
        self.graph.add_node("collect", self.summarizer_collect_node)

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

    # ---- Nodes ----

    def pdf_loader_node(self, state: IngestionState) -> IngestionState:
        state["document"] = self.pdf_loader.load(self.doc_name)
        return state

    def chunker_node(self, state: IngestionState) -> IngestionState:
        if not state["document"]:
            return state

        chunks = self.chunker.chunk_documents(state["document"], self.doc_name)
        chunks = attach_chunk_ids(chunks)

        for c in chunks:
            doc_title = self.doc_name
            chunk_title = c.get("metadata", {}).get("title") or f"chunk_{c['chunk_id']}"

            c["document"] = {"title": doc_title}
            c["content"] = {
                "title": chunk_title,
                "text": c["content"]
            }

        state["chunks"] = chunks
        state["filtered_chunks"] = chunks.copy()
        return state

    def toc_filter_node(self, state: IngestionState) -> IngestionState:
        if not state["filtered_chunks"]:
            return state

        state["filtered_chunks"] = [
            c for c in state["filtered_chunks"]
            if not c["metadata"].get("is_toc", False)
        ]
        return state

    def score_filter_node(self, state: IngestionState) -> IngestionState:
        if not state["filtered_chunks"]:
            return state

        state["filtered_chunks"] = [
            c for c in state["filtered_chunks"]
            if float(c.get("score", 0.0)) >= self.score_threshold
        ]
        return state

    def metadata_cleanup_node(self, state: IngestionState) -> IngestionState:
        if not state["filtered_chunks"]:
            return state

        state["filtered_chunks"] = [
            {**c, "metadata": dict(c.get("metadata", {}))}
            for c in state["filtered_chunks"]
        ]
        return state

    def summarizer_msg_builder_node(self, state: IngestionState) -> IngestionState:
        if not state["filtered_chunks"]:
            return state

        inputs = [
            {
                "chunk_id": c["chunk_id"],
                "title": c["content"]["title"],
                "content": c["content"]["text"]
            }
            for c in state["filtered_chunks"]
        ]

        messages = self.msg_builder.build_batch(
            prompt_file_name="summarizer",
            inputs=inputs
        )

        for i, msg in enumerate(messages):
            msg["chunk_id"] = inputs[i]["chunk_id"]

        state["messages"] = messages
        return state

    def summarizer_generate_node(self, state: IngestionState) -> IngestionState:
        if not state["messages"]:
            return state

        outputs = []
        for msg in state["messages"]:
            outputs.append({
                "chunk_id": msg["chunk_id"],
                "data": self.llm_generator.generate(msg["data"])
            })

        state["raw_summaries"] = outputs
        return state

    def summarizer_extract_node(self, state: IngestionState) -> IngestionState:
        if not state["raw_summaries"]:
            return state

        extracted_raw = self.json_extractor.extract_batch(
            [r["data"] for r in state["raw_summaries"]]
        )

        state["extracted"] = [
            {"chunk_id": state["raw_summaries"][i]["chunk_id"], "data": extracted_raw[i]}
            for i in range(len(extracted_raw))
        ]

        return state

    def summarizer_validate_node(self, state: IngestionState) -> IngestionState:
        if not state["extracted"]:
            return state

        extracted_data = [e["data"] for e in state["extracted"]]

        validated_raw = self.json_validator.validate_batch(
            extracted_data,
            required_keys=self.required_keys,
            allowed_flags=self.allowed_flags
        )

        state["validated"] = [
            {
                "chunk_id": state["extracted"][i]["chunk_id"],
                "data": validated_raw[i]["data"],
                "state": validated_raw[i]["state"]
            }
            for i in range(len(validated_raw))
        ]

        return state

    def summarizer_collect_node(self, state: IngestionState) -> IngestionState:
        if not state["validated"]:
            return state

        state["summary"] = [
            v for v in state["validated"] if v["state"]
        ]

        return state

    def embedding_node(self, state: IngestionState) -> IngestionState:
        if not state["filtered_chunks"]:
            return state

        texts = [c["content"]["text"] for c in state["filtered_chunks"]]
        embeddings = self.embedding.embed_batch(texts)

        state["embeddings"] = [
            {"chunk_id": state["filtered_chunks"][i]["chunk_id"], "vector": embeddings[i]}
            for i in range(len(embeddings))
        ]

        return state

    def final_aggregation_node(self, state: IngestionState) -> IngestionState:
        if not state["summary"]:
            return state

        summaries = state["summary"] or []
        embeddings = state.get("embeddings") or []
        filtered_chunks = state.get("filtered_chunks") or []

        summary_map = {s["chunk_id"]: s["data"] for s in summaries}
        embedding_map = {e["chunk_id"]: e["vector"] for e in embeddings}
        metadata_map = {c["chunk_id"]: c.get("metadata", {}) for c in filtered_chunks}
        document_map = {c["chunk_id"]: c.get("document", {}) for c in filtered_chunks}
        content_map = {c["chunk_id"]: c.get("content", {}) for c in filtered_chunks}

        documents = []

        for cid in summary_map:
            documents.append({
                "document": document_map.get(cid),
                "content": {
                    **content_map.get(cid, {}),
                    "summary": summary_map[cid]
                },
                "vector": embedding_map.get(cid),
                "metadata": metadata_map.get(cid)
            })

        pipeline_output = PipelineOutput(
            data=documents,
            meta=PipelineMeta(
                pipeline_version=PIPELINE_VERSION,
                count=len(documents)
            )
        )

        state["summary"] = [pipeline_output.model_dump()]
        return state

    # ---- Runner ----
    def run(self) -> IngestionState:
        initial_state: IngestionState = {
            "document": None,
            "chunks": None,
            "filtered_chunks": None,
            "messages": None,
            "raw_summaries": None,
            "extracted": None,
            "validated": None,
            "summary": None,
            "embeddings": None,
        }

        return self.compiled.invoke(initial_state)  # type: ignore