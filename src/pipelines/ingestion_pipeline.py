# ---- Imports ----
from typing import TypedDict
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

# ---- Config ----
DOC_NAME = "Millennial_Playbook_Full.pdf"
DOC_NAME = "Ai System Design Competition.pdf"


# ---- State Definition ----
class IngestionState(TypedDict):
    document: list[Document] | None
    chunks: list[dict] | None
    messages: list[dict] | None
    summary: list[str] | None
    embeddings: list[list[float]] | None


# ---- Nodes (Functions) ----

def pdf_loader_node(state: IngestionState) -> IngestionState:
    loader = get_pdf_loader()
    state["document"] = loader.load(DOC_NAME)
    return state


def chunker_node(state: IngestionState) -> IngestionState:
    chunker = get_chunker()

    if not state["document"]:
        raise ValueError("No document loaded")

    state["chunks"] = chunker.chunk_documents(state["document"], DOC_NAME)
    # print("chunks: ", state["chunks"])
    return state

def summarizer_msg_builder_node(state: IngestionState) -> IngestionState:
    msg_builder = get_msg_builder()

    if not state["chunks"]:
        raise ValueError("No chunks available")

    # ---- Build Batch Inputs ----
    inputs = [
        {
            "topic": chunk["doc_name"],
            "content": chunk["content"],
        }
        for chunk in state["chunks"]
    ]

    # ---- Build Messages Batch ----
    batch_messages = msg_builder.build_batch(
        prompt_file_name="summarizer",
        inputs=inputs,
    )

    # ---- Attach to State ----
    state["messages"] = batch_messages
    # print("batch_messages: ", batch_messages)

    # print("messages: ", state["messages"])
    return state

# ---- Node ----
def summarizer_generator_node(state: IngestionState) -> IngestionState:
    summarizer = get_llm_generator()
    validator = get_llm_json_validator()
    extractor = get_llm_json_extractor()

    batch_messages = state.get("messages")
    if batch_messages is None or len(batch_messages) == 0:
        raise ValueError("No messages available")

    # ---- Define Output Schema (CRITICAL FIX) ----
    required_keys = {"title", "summary", "flag"}
    allowed_flags = {"SUCCESS_FLAG"}

    # ---- Generate ----
    summarized_chunks = [
        summarizer.generate(msg["data"])
        for msg in batch_messages
    ]

    # ---- Extract ----
    extracted_chunk_data = extractor.extract_batch(summarized_chunks)

    # ---- Validate ----
    validated_chunks = validator.validate_batch(
        extracted_chunk_data,
        required_keys=required_keys,
        allowed_flags=allowed_flags,
    )

    # ---- Collect Only Valid ----
    state["summary"] = [
        item["data"]
        for item in validated_chunks
        if item["state"]
    ]
    return state


def embedding_node(state: IngestionState) -> IngestionState:
    embedding_model = get_embedding()

    if not state["chunks"]:
        raise ValueError("No chunks available")

    texts = [chunk["content"] for chunk in state["chunks"]]
    state["embeddings"] = embedding_model.embed_batch(texts)
    print("embeddings: ", state["embeddings"])

    return state


# ---- Pipeline Orchestrator Class ----
class IngestionPipeline:
    # ---- Initialize ----
    def __init__(self) -> None:
        self.graph = StateGraph(IngestionState)
        self._register_nodes()
        self._build_graph()
        self.compiled = self.graph.compile()

    # ---- Register Nodes ----
    def _register_nodes(self) -> None:
        self.graph.add_node("pdf_loader", pdf_loader_node)
        self.graph.add_node("chunker", chunker_node)
        self.graph.add_node("summarizer_msg_builder", summarizer_msg_builder_node)
        self.graph.add_node("summarizer_generator", summarizer_generator_node)
        self.graph.add_node("embedding", embedding_node)

    # ---- Build Graph ----
    def _build_graph(self) -> None:
        self.graph.add_edge(START, "pdf_loader")
        self.graph.add_edge("pdf_loader", "chunker")
        self.graph.add_edge("chunker", "summarizer_msg_builder")
        self.graph.add_edge("summarizer_msg_builder", "summarizer_generator")
        self.graph.add_edge("summarizer_generator", "embedding")
        self.graph.add_edge("embedding", END)

    # ---- Run Pipeline ----
    def run(self) -> IngestionState:
        initial_state: IngestionState = {
            "document": None,
            "chunks": None,
            "summary": None,
            "messages": None,
            "embeddings": None,
        }

        return self.compiled.invoke(initial_state) # type: ignore


# ---- Entry Point ----
if __name__ == "__main__":
    pipeline = IngestionPipeline()
    result = pipeline.run()