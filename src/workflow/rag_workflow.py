# ---- Imports ----
import logging
from typing import TypedDict, Any

from langgraph.graph import StateGraph, START, END
from src.shared.graph_builder import GraphSaver

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- State ----
class RAGState(TypedDict):
    question: str
    retrieved_docs: list[dict] | None
    chunks: str | None
    final_output: Any | None


# ---- RAG Workflow ----
class RAGWorkflow:

    # ---- Constructor ----
    def __init__(self, aug_gen_pipeline, hybrid_retriever):
        self.aug_gen_pipeline = aug_gen_pipeline
        self.hybrid_retriever = hybrid_retriever

        self.graph = StateGraph(RAGState)
        self._build_graph()

        self.compiled = self.graph.compile()
        self.graph_saver = GraphSaver("rag_workflow.png")

    # ---- Graph Builder ----
    def _build_graph(self) -> None:

        self.graph.add_node("retrieve", self.retrieve_node)
        self.graph.add_node("extract_chunks", self.extract_chunks_node)
        self.graph.add_node("augment_generate", self.augment_generate_node)

        self.graph.add_edge(START, "retrieve")
        self.graph.add_edge("retrieve", "extract_chunks")
        self.graph.add_edge("extract_chunks", "augment_generate")
        self.graph.add_edge("augment_generate", END)

    # ---- Node: Retrieve ----
    async def retrieve_node(self, state: RAGState) -> RAGState:

        docs = await self.hybrid_retriever.search(
            input_query=state["question"]
        )

        if not isinstance(docs, list):
            raise TypeError(f"Retriever must return list, got {type(docs)}")

        state["retrieved_docs"] = docs

        logger.info(f"Retrieved docs: {len(docs)}")

        return state

    # ---- Node: Extract Chunks ----
    async def extract_chunks_node(self, state: RAGState) -> RAGState:

        docs = state.get("retrieved_docs") or []

        chunks = " ".join(
            (d.get("content") or "").strip()
            for d in docs
            if isinstance(d, dict)
        )

        state["chunks"] = chunks

        logger.info(f"Chunks length: {len(chunks)}")

        return state

    # ---- Node: Augment + Generate ----
    async def augment_generate_node(self, state: RAGState) -> RAGState:

        result = await self.aug_gen_pipeline.run(
            queries=[
                {
                    "user_question": state["question"],
                    "chunks": state.get("chunks") or "",
                }
            ]
        )

        state["final_output"] = result

        logger.info("Generation completed")

        return state

    # ---- Runner ----
    async def run(self, question: str):

        initial_state: RAGState = {
            "question": question,
            "retrieved_docs": None,
            "chunks": None,
            "final_output": None,
        }
        self.graph_saver.save(self.compiled)
        return await self.compiled.ainvoke(initial_state)  # type: ignore