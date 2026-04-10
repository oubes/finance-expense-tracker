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

    # ---- Policy Layer ----
    flag: Literal["RAG_FLAG", "REJECTION_FLAG", "CHAT_FLAG"] | None
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
        self.graph.add_node("retrieve", self.retrieve_node)
        self.graph.add_node("safe_generation", self.safe_generation_node)
        self.graph.add_node("chat_node", self.chat_node)
        self.graph.add_node("rejection_node", self.rejection_node)

        # ---- Entry ----
        self.graph.add_edge(START, "policy_router")

        # ---- Conditional Routing ----
        self.graph.add_conditional_edges(
            "policy_router",
            self._route_decision,
            {
                "REJECTION_FLAG": "rejection_node",
                "CHAT_FLAG": "chat_node",
                "RAG_FLAG": "retrieve",
            },
        )

        # ---- RAG Path ----
        self.graph.add_edge("retrieve", "safe_generation")
        self.graph.add_edge("safe_generation", END)

        # ---- Terminal Paths ----
        self.graph.add_edge("chat_node", END)
        self.graph.add_edge("rejection_node", END)

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

            print(f"\n\n=========> policy_router result={result} <=========\n\n")

            state["flag"] = payload.get("flag")
            state["reason"] = payload.get("reason")
            state["chat_response"] = payload.get("chat_response")

            print(f"=========> flag={state['flag']} reason={state['reason']} <=========")

            logger.info(
                f"[policy_router] flag={state['flag']} reason={state['reason']}"
            )

        except Exception as e:
            logger.exception(f"[policy_router] failed: {e}")
            state["flag"] = "REJECTION_FLAG"
            state["reason"] = "policy_router_error"
            state["chat_response"] = None

        return state

    # ---- Chat Node ----
    async def chat_node(self, state: RAGState) -> RAGState:
        logger.info("[chat_node] start")

        try:
            state["final_output"] = {
                "response": state.get("chat_response"),
                "flag": state.get("flag"),
                "reason": state.get("reason"),
            }

            logger.info("[chat_node] completed")

        except Exception as e:
            logger.exception(f"[chat_node] failed: {e}")
            state["final_output"] = {
                "response": None,
                "flag": "CHAT_FLAG",
                "reason": "chat_node_error",
            }

        print(f"=========> {state['final_output']} <=========")
        return state

    # ---- Rejection Node ----
    async def rejection_node(self, state: RAGState) -> RAGState:
        logger.info("[rejection_node] start")

        try:
            state["final_output"] = {
                "response": state.get("reason"),
                "flag": state.get("flag"),
                "reason": state.get("reason"),
            }

            logger.info("[rejection_node] completed")

        except Exception as e:
            logger.exception(f"[rejection_node] failed: {e}")
            state["final_output"] = {
                "response": "Request rejected.",
                "flag": "REJECTION_FLAG",
                "reason": "rejection_node_error",
            }

        print(f"=========> {state['final_output']} <=========")
        return state

    # ---- Retrieve Node ----
    async def retrieve_node(self, state: RAGState) -> RAGState:
        logger.info("[retrieve] start")

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

            logger.info("[retrieve] completed")

        except Exception as e:
            logger.exception(f"[retrieve] failed: {e}")
            state["chunks"] = ""

        return state

    # ---- Safe Generation Node ----
    async def safe_generation_node(self, state: RAGState) -> RAGState:
        logger.info("[safe_generation] start")

        try:
            result = await self.safe_generator.run(
                prompt_file_name="aug_gen",
                user_question=state["user_query"],
                context=state.get("chunks") or "",
            )

            state["final_output"] = {
                "response": result,
                "flag": state.get("flag"),
                "reason": state.get("reason"),
            }

            logger.info("[safe_generation] completed")

        except Exception as e:
            logger.exception(f"[safe_generation] failed: {e}")
            state["final_output"] = {
                "response": None,
                "flag": state.get("flag"),
                "reason": state.get("reason"),
            }

        print(f"=========> {state['final_output']} <=========")

        return state

    # ---- Runner ----
    async def run(self, user_query: str):

        initial_state: RAGState = {
            "user_query": user_query,
            "chunks": None,
            "flag": None,
            "reason": None,
            "chat_response": None,
            "final_output": None,
        }

        self.graph_saver.save(self.compiled)

        return await self.compiled.ainvoke(initial_state)  # type: ignore