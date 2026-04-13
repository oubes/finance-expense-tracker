# ---- Imports ----
import logging
from typing import TypedDict, Any, Literal

from langgraph.graph import StateGraph, START, END
from src.shared.graph_builder import GraphSaver

logger = logging.getLogger(__name__)


# ---- State ----
class RAGState(TypedDict):
    user_query: str  # READ-ONLY

    # router output
    flag: Literal["CHAT_FLAG", "REJECTION_FLAG"] | None
    reason: str | None
    summary: str | None

    # chat routing
    chat_mode: Literal[
        "NORMAL_FLAG",
        "MEMORY_FLAG",
        "RAG_FLAG",
        "MEMORY_RAG_FLAG"
    ] | None

    chat_response: Any | None
    rejection_reason: str | None

    final_output: Any | None


# ---- Workflow ----
class RAGWorkflow:

    def __init__(
        self,
        safe_generator,
        hybrid_retriever,
        embedder,
        semantic_memory,
        user_facts_memory,
        transactions_memory,
    ):
        self.safe_generator = safe_generator
        self.embedder = embedder

        self.semantic_memory = semantic_memory
        self.user_facts_memory = user_facts_memory
        self.transactions_memory = transactions_memory
        self.book_retriever = hybrid_retriever

        self.graph = StateGraph(RAGState)
        self._build_graph()

        self.compiled = self.graph.compile()
        self.graph_saver = GraphSaver("rag_workflow.png")

    # ---- Graph ----
    def _build_graph(self):

        self.graph.add_node("policy_router", self.policy_router_node)
        self.graph.add_node("chat_router", self.chat_router_node)

        self.graph.add_node("normal_chat", self.normal_chat_node)
        self.graph.add_node("memory_chat", self.memory_chat_node)
        self.graph.add_node("rag_chat", self.rag_chat_node)
        self.graph.add_node("memory_rag_chat", self.memory_rag_chat_node)

        self.graph.add_node("rejection_node", self.rejection_node)
        self.graph.add_node("output_node", self.output_node)

        self.graph.add_edge(START, "policy_router")

        self.graph.add_conditional_edges(
            "policy_router",
            self._route_main,
            {
                "CHAT_FLAG": "chat_router",
                "REJECTION_FLAG": "rejection_node",
            },
        )

        self.graph.add_conditional_edges(
            "chat_router",
            self._route_chat,
            {
                "NORMAL_FLAG": "normal_chat",
                "MEMORY_FLAG": "memory_chat",
                "RAG_FLAG": "rag_chat",
                "MEMORY_RAG_FLAG": "memory_rag_chat",
            },
        )

        self.graph.add_edge("normal_chat", "output_node")
        self.graph.add_edge("memory_chat", "output_node")
        self.graph.add_edge("rag_chat", "output_node")
        self.graph.add_edge("memory_rag_chat", "output_node")

        self.graph.add_edge("rejection_node", "output_node")
        self.graph.add_edge("output_node", END)

    # ---- Routers ----
    def _route_main(self, state: RAGState) -> str:
        return state.get("flag") or "REJECTION_FLAG"

    def _route_chat(self, state: RAGState) -> str:
        return state.get("chat_mode") or "NORMAL_FLAG"

    # ---- Policy Router ----
    async def policy_router_node(self, state: RAGState) -> RAGState:
        logger.info("[ENTER_NODE] policy_router")

        try:
            result = await self.safe_generator.run(
                prompt_file_name="policy_router",
                content=state["user_query"],
                required_keys={"flag", "summary", "reason"},
                allowed_flags={"CHAT_FLAG", "REJECTION_FLAG"},
                temperature=0.0,
            )

            payload = result.get("data") if isinstance(result.get("data"), dict) else result

            state["flag"] = payload.get("flag")
            state["reason"] = payload.get("reason")
            state["summary"] = payload.get("summary")

        except Exception:
            logger.exception("[policy_router] failure")
            state["flag"] = "REJECTION_FLAG"
            state["reason"] = "router_error"

        return state.copy()

    # ---- Chat Router ----
    async def chat_router_node(self, state: RAGState) -> RAGState:
        logger.info("[ENTER_NODE] chat_router")
        
        embedded_query = await self.embedder.embed(state["user_query"])
        
        await self.semantic_memory.add_message(
            user_id="1",
            role="user",
            content=state["user_query"],
            embedding=embedded_query,
        )

        try:
            result = await self.safe_generator.run(
                prompt_file_name="chat_router",
                content=state["summary"] or state["user_query"],
                required_keys={"chat_mode", "reason"},
                allowed_flags={
                    "NORMAL_FLAG",
                    "MEMORY_FLAG",
                    "RAG_FLAG",
                    "MEMORY_RAG_FLAG",
                },
                temperature=0.0,
            )
            
            print(f"\n\n=========> CHAT ROUTER RESULT: {result} <=========\n\n")

            payload = result.get("data") if isinstance(result.get("data"), dict) else result

            state["chat_mode"] = payload.get("chat_mode")

        except Exception:
            logger.exception("[chat_router] failure")
            state["chat_mode"] = "NORMAL_FLAG"

        return state.copy()

    # ---- CHAT NODES ----
    async def normal_chat_node(self, state: RAGState) -> RAGState:
        result = await self.safe_generator.run(
            prompt_file_name="chat_normal",
            content=state["user_query"],
            temperature=0.0,
        )

        state["chat_response"] = (
            result.get("data", {}).get("response")
            if isinstance(result.get("data"), dict)
            else None
        )

        return state.copy()

    async def memory_chat_node(self, state: RAGState) -> RAGState:
        last_messages_raw = await self.semantic_memory.get_stm(user_id="1", limit=10)

        last_messages = [
            {"role": r[2], "content": r[3], "date": r[5]}
            for r in (last_messages_raw or [])
        ]

        result = await self.safe_generator.run(
            prompt_file_name="chat_memory",
            content=state["user_query"],
            past_conversation=last_messages,
            temperature=0.0,
        )
        extracted_response = result.get("data", {}).get("response") if isinstance(result.get("data"), dict) else None
        
        embedded_response = await self.embedder.embed(extracted_response)
        await self.semantic_memory.add_message(
            user_id="1",
            role="ai",
            content=extracted_response,
            embedding=embedded_response,
        )

        state["chat_response"] = extracted_response
        return state.copy()

    async def rag_chat_node(self, state: RAGState) -> RAGState:
        raw_docs = await self.book_retriever.search(
            state["user_query"],
            limit=5,
        )
        
        docs = [
            {"content": d.get("summary") or d.get("content")}
            for d in (raw_docs or [])
        ]
        
        print(f"\n\n=========> RETRIEVED DOCS: {docs} <=========\n\n")

        result = await self.safe_generator.run(
            prompt_file_name="chat_rag",
            content=state["user_query"],
            chunks=docs,
            temperature=0.0,
        )

        state["chat_response"] = result.get("data", {}).get("response")
        return state.copy()

    async def memory_rag_chat_node(self, state: RAGState) -> RAGState:
        last_messages_raw = await self.semantic_memory.get_stm(user_id="1", limit=10)

        last_messages = [
            {"role": r[2], "content": r[3], "date": r[5]}
            for r in (last_messages_raw or [])
        ]
        
        print(f"\n\n=========> LAST MESSAGES: {last_messages} <=========\n\n")

        raw_docs = await self.book_retriever.search(
            state["user_query"],
            limit=5,
        )
        
        docs = [
            {"content": d.get("summary") or d.get("content")}
            for d in (raw_docs or [])
        ]
        
        print(f"\n\n=========> RETRIEVED DOCS: {docs} <=========\n\n")

        result = await self.safe_generator.run(
            prompt_file_name="chat_memory_rag",
            content=state["user_query"],
            past_conversation=last_messages,
            chunks=docs,
            temperature=0.0,
        )

        state["chat_response"] = result.get("data", {}).get("response")
        return state.copy()

    # ---- REJECTION ----
    async def rejection_node(self, state: RAGState) -> RAGState:
        state["rejection_reason"] = state.get("reason")
        return state.copy()

    # ---- OUTPUT ----
    async def output_node(self, state: RAGState) -> RAGState:
        state["final_output"] = {
            "flag": state.get("flag"),
            "chat_mode": state.get("chat_mode"),
            "reason": state.get("reason"),
            "summary": state.get("summary"),
            "response": state.get("chat_response")
            if state.get("flag") == "CHAT_FLAG"
            else state.get("rejection_reason"),
        }

        return state.copy()

    # ---- RUN ----
    async def run(self, user_query: str):

        initial_state: RAGState = {
            "user_query": user_query,
            "flag": None,
            "reason": None,
            "summary": None,
            "chat_mode": None,
            "chat_response": None,
            "rejection_reason": None,
            "final_output": None,
        }

        logger.info("[WORKFLOW_START]")

        self.graph_saver.save(self.compiled)

        return await self.compiled.ainvoke(initial_state)