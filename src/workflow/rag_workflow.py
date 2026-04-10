# ---- Imports ----
import logging
from typing import TypedDict, Any, Literal

from langgraph.graph import StateGraph, START, END
from src.shared.graph_builder import GraphSaver


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- State ----
class RAGState(TypedDict):
    user_query: str

    chunks: str | None
    memory: str | None
    context: str | None

    # ---- Policy Layer ----
    flag: Literal[
        "RAG_FLAG",
        "REJECTION_FLAG",
        "CHAT_FLAG",
        "MEMORY_FLAG",
        "RAG_AND_MEMORY_FLAG",
    ] | None

    reason: str | None
    chat_response: str | None

    # ---- Output ----
    final_output: Any | None


# ---- Workflow ----
class RAGWorkflow:

    def __init__(
        self,
        safe_generator,
        hybrid_retriever,
    ):
        self.safe_generator = safe_generator
        self.hybrid_retriever = hybrid_retriever

        self.graph = StateGraph(RAGState)
        self._build_graph()

        self.compiled = self.graph.compile()
        self.graph_saver = GraphSaver("rag_workflow.png")

    # ---- Graph Definition ----
    def _build_graph(self) -> None:

        # ---- Nodes ----
        self.graph.add_node("policy_router", self.policy_router_node)

        self.graph.add_node("chat_node", self.chat_node)
        self.graph.add_node("rejection_node", self.rejection_node)

        self.graph.add_node("pull_memory", self.pull_memory_node)
        self.graph.add_node("rag_and_mem_pull_mem", self.rag_and_mem_pull_mem_node)

        # ---- Split Retrieval Nodes ----
        self.graph.add_node("rag_retrieve", self.rag_retrieve_node)
        self.graph.add_node("rag_and_mem_retrieve", self.rag_and_mem_retrieve_node)

        self.graph.add_node("safe_generation", self.safe_generation_node)

        # ---- Entry ----
        self.graph.add_edge(START, "policy_router")

        # ---- Routing ----
        self.graph.add_conditional_edges(
            "policy_router",
            self._route_decision,
            {
                "CHAT_FLAG": "chat_node",
                "REJECTION_FLAG": "rejection_node",
                "MEMORY_FLAG": "pull_memory",
                "RAG_FLAG": "rag_retrieve",
                "RAG_AND_MEMORY_FLAG": "rag_and_mem_pull_mem",
            },
        )

        # ---- MEMORY PATH ----
        self.graph.add_edge("pull_memory", "safe_generation")

        # ---- RAG PATH ----
        self.graph.add_edge("rag_retrieve", "safe_generation")

        # ---- RAG + MEMORY PATH ----
        self.graph.add_edge("rag_and_mem_pull_mem", "rag_and_mem_retrieve")
        self.graph.add_edge("rag_and_mem_retrieve", "safe_generation")

        # ---- TERMINALS ----
        self.graph.add_edge("chat_node", END)
        self.graph.add_edge("rejection_node", END)
        self.graph.add_edge("safe_generation", END)

    # ---- Router Logic ----
    def _route_decision(self, state: RAGState) -> str:
        return state.get("flag") or "REJECTION_FLAG"

    # ---- Policy Router Node ----
    async def policy_router_node(self, state: RAGState) -> RAGState:
        logger.info("[policy_router] start")

        try:
            result = await self.safe_generator.run(
                prompt_file_name="policy_router",
                content=state["user_query"],
                context="",
            )

            payload = result.get("data") if isinstance(result.get("data"), dict) else result

            state["flag"] = payload.get("flag")
            state["reason"] = payload.get("reason")
            state["chat_response"] = payload.get("chat_response")
            state["context"] = payload.get("context")

        except Exception as e:
            logger.exception(f"[policy_router] failed: {e}")
            state["flag"] = "REJECTION_FLAG"
            state["reason"] = "policy_router_error"
            state["chat_response"] = None
            state["context"] = None

        return state

    # ---- Chat Node ----
    async def chat_node(self, state: RAGState) -> RAGState:
        state["final_output"] = {
            "response": state.get("chat_response"),
            "flag": state.get("flag"),
            "reason": state.get("reason"),
        }
        return state

    # ---- Rejection Node ----
    async def rejection_node(self, state: RAGState) -> RAGState:
        state["final_output"] = {
            "response": state.get("reason"),
            "flag": state.get("flag"),
            "reason": state.get("reason"),
        }
        return state

    # ---- MEMORY Node ----
    async def pull_memory_node(self, state: RAGState) -> RAGState:
        state["memory"] = ""
        return state

    # ---- RAG + MEMORY MEMORY STAGE ----
    async def rag_and_mem_pull_mem_node(self, state: RAGState) -> RAGState:
        state["memory"] = ""
        return state

    # ---- RAG RETRIEVE (dedicated) ----
    async def rag_retrieve_node(self, state: RAGState) -> RAGState:
        logger.info("[rag_retrieve] start")

        try:
            chunks = await self.hybrid_retriever.search(
                input_query=state["user_query"],
                limit=1,
            )

            state["chunks"] = " ".join(
                (d.get("content") or "").strip()
                for d in chunks
                if isinstance(d, dict)
            )

        except Exception as e:
            logger.exception(f"[rag_retrieve] failed: {e}")
            state["chunks"] = ""

        return state

    # ---- RAG + MEMORY RETRIEVE (dedicated) ----
    async def rag_and_mem_retrieve_node(self, state: RAGState) -> RAGState:
        logger.info("[rag_and_mem_retrieve] start")

        try:
            chunks = await self.hybrid_retriever.search(
                input_query=state["user_query"],
                limit=1,
            )

            state["chunks"] = " ".join(
                (d.get("content") or "").strip()
                for d in chunks
                if isinstance(d, dict)
            )

        except Exception as e:
            logger.exception(f"[rag_and_mem_retrieve] failed: {e}")
            state["chunks"] = ""

        return state

    # ---- Safe Generation Node ----
    async def safe_generation_node(self, state: RAGState) -> RAGState:
        logger.info("[safe_generation] start")

        try:
            result = await self.safe_generator.run(
                prompt_file_name="aug_gen",
                user_question=state["user_query"],
                context=(state.get("chunks") or "") + (state.get("memory") or ""),
            )

            state["final_output"] = {
                "response": result,
                "flag": state.get("flag"),
                "reason": state.get("reason"),
            }

        except Exception as e:
            logger.exception(f"[safe_generation] failed: {e}")
            state["final_output"] = {
                "response": None,
                "flag": state.get("flag"),
                "reason": state.get("reason"),
            }

        return state

    # ---- Runner ----
    async def run(self, user_query: str):

        initial_state: RAGState = {
            "user_query": user_query,
            "chunks": None,
            "context": None,
            "memory": None,
            "flag": None,
            "reason": None,
            "chat_response": None,
            "final_output": None,
        }

        self.graph_saver.save(self.compiled)

        return await self.compiled.ainvoke(initial_state)  # type: ignore