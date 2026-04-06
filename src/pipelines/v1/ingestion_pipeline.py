# ---- Imports ----
from typing import TypedDict, Any
import logging
import uuid

from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END

from src.bootstrap.dependencies import (
    get_pdf_loader,
    get_chunker,
    get_embedding,
    get_llm_generator,
    get_msg_builder,
    get_llm_json_extractor,
    get_llm_json_validator
)

# ---- Logger ----
logger = logging.getLogger(__name__)

# ---- Config ----
DOC_NAME = "Ai System Design Competition.pdf"
SCORE_THRESHOLD = 0.5
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

    summary: list[dict] | None
    embeddings: list[dict] | None


# ---- Utility ----
def attach_chunk_ids(chunks: list[dict]) -> list[dict]:
    # ---- Assign IDs ----
    for c in chunks:
        c["chunk_id"] = str(uuid.uuid4())
    return chunks


# ---- Load PDF ----
def pdf_loader_node(state: IngestionState) -> IngestionState:
    loader = get_pdf_loader()
    state["document"] = loader.load(DOC_NAME)

    if not state["document"]:
        logger.warning("No documents loaded")

    return state


# ---- Chunk ----
def chunker_node(state: IngestionState) -> IngestionState:
    chunker = get_chunker()

    if not state["document"]:
        logger.warning("No document")
        return state

    chunks = chunker.chunk_documents(state["document"], DOC_NAME)
    chunks = attach_chunk_ids(chunks)

    # ---- Normalize titles ----
    for c in chunks:
        # document-level title (book)
        doc_title = DOC_NAME

        # chunk-level title (section if exists, else fallback)
        chunk_title = c.get("metadata", {}).get("title") or f"chunk_{c['chunk_id']}"

        c["document"] = {
            "title": doc_title
        }

        c["content"] = {
            "title": chunk_title,
            "text": c["content"]
        }

    state["chunks"] = chunks
    state["filtered_chunks"] = chunks.copy()

    return state


# ---- Filter TOC + Cleanup ----
def toc_filter_node(state: IngestionState) -> IngestionState:
    if not state["filtered_chunks"]:
        return state

    valid_chunks = [
        c for c in state["filtered_chunks"]
        if not c["metadata"].get("is_toc", False)
    ]

    removed_ids = {c["chunk_id"] for c in state["filtered_chunks"]} - {c["chunk_id"] for c in valid_chunks}

    state["filtered_chunks"] = valid_chunks

    if removed_ids:
        _cleanup_by_ids(state, removed_ids)

    return state


# ---- Score Filter + Cleanup ----
def score_filter_node(state: IngestionState) -> IngestionState:
    if not state["filtered_chunks"]:
        return state

    valid_chunks = [
        c for c in state["filtered_chunks"]
        if float(c.get("score", 0.0)) >= SCORE_THRESHOLD
    ]

    removed_ids = {c["chunk_id"] for c in state["filtered_chunks"]} - {c["chunk_id"] for c in valid_chunks}

    state["filtered_chunks"] = valid_chunks

    if removed_ids:
        _cleanup_by_ids(state, removed_ids)

    return state


# ---- Cleanup Helper ----
def _cleanup_by_ids(state: IngestionState, removed_ids: set[str]) -> None:
    if state.get("messages"):
        state["messages"] = [m for m in state["messages"] if m.get("chunk_id") not in removed_ids]

    if state.get("raw_summaries"):
        state["raw_summaries"] = [r for r in state["raw_summaries"] if r.get("chunk_id") not in removed_ids]

    if state.get("extracted"):
        state["extracted"] = [e for e in state["extracted"] if e.get("chunk_id") not in removed_ids]

    if state.get("validated"):
        state["validated"] = [v for v in state["validated"] if v.get("chunk_id") not in removed_ids]

    if state.get("embeddings"):
        state["embeddings"] = [e for e in state["embeddings"] if e.get("chunk_id") not in removed_ids]


# ---- Metadata Cleanup ----
def metadata_cleanup_node(state: IngestionState) -> IngestionState:
    if not state["filtered_chunks"]:
        return state

    state["filtered_chunks"] = [
        {**c, "metadata": dict(c.get("metadata", {}))}
        for c in state["filtered_chunks"]
    ]

    return state


# ---- Build Messages ----
def summarizer_msg_builder_node(state: IngestionState) -> IngestionState:
    builder = get_msg_builder()

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

    messages = builder.build_batch(
        prompt_file_name="summarizer",
        inputs=inputs
    )

    for i, msg in enumerate(messages):
        msg["chunk_id"] = inputs[i]["chunk_id"]

    state["messages"] = messages
    return state


# ---- Generate ----
def summarizer_generate_node(state: IngestionState) -> IngestionState:
    generator = get_llm_generator()

    if not state["messages"]:
        return state

    outputs = []
    for msg in state["messages"]:
        outputs.append({
            "chunk_id": msg["chunk_id"],
            "data": generator.generate(msg["data"])
        })

    state["raw_summaries"] = outputs
    return state


# ---- Extract ----
def summarizer_extract_node(state: IngestionState) -> IngestionState:
    extractor = get_llm_json_extractor()

    if not state["raw_summaries"]:
        return state

    extracted_raw = extractor.extract_batch([r["data"] for r in state["raw_summaries"]])

    state["extracted"] = [
        {"chunk_id": state["raw_summaries"][i]["chunk_id"], "data": extracted_raw[i]}
        for i in range(len(extracted_raw))
    ]

    return state


# ---- Validate ----
def summarizer_validate_node(state: IngestionState) -> IngestionState:
    validator = get_llm_json_validator()

    if not state["extracted"]:
        return state

    required_keys = {"title", "summary", "flag"}
    allowed_flags = {"SUCCESS_FLAG"}

    extracted_data = [e["data"] for e in state["extracted"]]

    validated_raw = validator.validate_batch(
        extracted_data,
        required_keys=required_keys,
        allowed_flags=allowed_flags
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


# ---- Collect ----
def summarizer_collect_node(state: IngestionState) -> IngestionState:
    if not state["validated"]:
        return state

    state["summary"] = [
        v for v in state["validated"] if v["state"]
    ]

    return state


# ---- Embedding ----
def embedding_node(state: IngestionState) -> IngestionState:
    model = get_embedding()

    if not state["filtered_chunks"]:
        return state

    texts = [c["content"]["text"] for c in state["filtered_chunks"]]
    embeddings = model.embed_batch(texts)

    state["embeddings"] = [
        {"chunk_id": state["filtered_chunks"][i]["chunk_id"], "vector": embeddings[i]}
        for i in range(len(embeddings))
    ]

    return state


# ---- Final Aggregator ----
def final_aggregation_node(state: IngestionState) -> IngestionState:
    if not state["summary"]:
        return state

    summaries = state["summary"]
    embeddings = state.get("embeddings", [])
    filtered_chunks = state.get("filtered_chunks", [])

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

    state["summary"] = [
        {
            "data": documents,
            "meta": {
                "pipeline_version": PIPELINE_VERSION,
                "count": len(documents)
            }
        }
    ]

    return state


# ---- Pipeline ----
class IngestionPipeline:

    def __init__(self) -> None:
        self.graph = StateGraph(IngestionState)
        self._register_nodes()
        self._build_graph()
        self.compiled = self.graph.compile()

    def _register_nodes(self) -> None:
        self.graph.add_node("pdf_loader", pdf_loader_node)
        self.graph.add_node("chunker", chunker_node)
        self.graph.add_node("toc_filter", toc_filter_node)
        self.graph.add_node("score_filter", score_filter_node)
        self.graph.add_node("metadata_cleanup", metadata_cleanup_node)

        self.graph.add_node("msg_builder", summarizer_msg_builder_node)
        self.graph.add_node("generate", summarizer_generate_node)
        self.graph.add_node("extract", summarizer_extract_node)
        self.graph.add_node("validate", summarizer_validate_node)
        self.graph.add_node("collect", summarizer_collect_node)

        self.graph.add_node("embedding", embedding_node)
        self.graph.add_node("final_aggregation", final_aggregation_node)

    def _build_graph(self) -> None:
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


# ---- Entry ----
if __name__ == "__main__":
    pipeline = IngestionPipeline()
    result = pipeline.run()

    print(f"Final Result: {result['summary']}")