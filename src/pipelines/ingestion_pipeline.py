# ---- Imports ----
from typing import TypedDict
from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END

from src.bootstrap.dependencies import (
    get_pdf_loader,
    get_chunker,
    get_embedding,
    get_llm_generator,
    get_msg_builder
)

# ---- Config ----
DOC_NAME = "Millennial_Playbook_Full.pdf"
DOC_NAME = "Ai System Design Competition.pdf"


# ---- State Definition ----
class IngestionState(TypedDict):
    document: list[Document] | None
    chunks: list[dict] | None
    summary: list[str] | None
    messages: list[dict] | None
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

def summarizer_build_node(state: IngestionState) -> IngestionState:
    msg_builder = get_msg_builder()

    if not state["chunks"]:
        raise ValueError("No chunks available")

    variables = {
        "topic": state["chunks"][0]["doc_name"],
        "content": "\n\n".join(chunk["content"] for chunk in state["chunks"]),
    }

    messages = msg_builder.build(
        prompt_file_name="summarizer",
        **variables,
    )

    state["messages"] = messages
    print("messages: ", state["messages"])

    return state

def summarizer_execute_node(state: IngestionState) -> IngestionState:
    summarizer = get_llm_generator()

    if "messages" not in state or not state["messages"]:
        raise ValueError("No messages found in state")

    batch_messages = [state["messages"]]

    outputs = summarizer.generate_batch(batch_messages)

    state["summary"] = outputs
    print("summary: ", state["summary"])

    return state


def embedding_node(state: IngestionState) -> IngestionState:
    embedding_model = get_embedding()

    if not state["chunks"]:
        raise ValueError("No chunks available")

    texts = [chunk["content"] for chunk in state["chunks"]]
    state["embeddings"] = embedding_model.embed_batch(texts)

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
        self.graph.add_node("summarizer_build", summarizer_build_node)
        self.graph.add_node("summarizer_execute", summarizer_execute_node)
        # self.graph.add_node("embedding", embedding_node)

    # ---- Build Graph ----
    def _build_graph(self) -> None:
        self.graph.add_edge(START, "pdf_loader")
        self.graph.add_edge("pdf_loader", "chunker")
        self.graph.add_edge("chunker", "summarizer_build")
        self.graph.add_edge("summarizer_build", "summarizer_execute")
        self.graph.add_edge("summarizer_execute", END)
        # self.graph.add_edge("embedding", END)

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