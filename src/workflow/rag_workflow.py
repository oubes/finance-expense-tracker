# ---- Imports ----
import logging
from typing import TypedDict, Any, Literal

from langgraph.graph import StateGraph, START, END
from src.shared.graph_builder import GraphSaver

logger = logging.getLogger(__name__)


# ---- State ----
class RAGState(TypedDict):
    user_query: str  # READ-ONLY

    # main router output
    flag: Literal["CHAT_FLAG", "REJECTION_FLAG"] | None
    reason: str | None
    summary: str | None

    # chat routing
    chat_mode: Literal[
        "NORMAL_FLAG",
        "MEMORY_FLAG",
        "RAG_FLAG",
        "MEMORY_RAG_FLAG",
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

    # ---- FIX: unified extraction layer ONLY ----
    def _normalize_memory_row(self, r):
        if isinstance(r, dict):
            return {
                "role": r.get("role"),
                "content": r.get("content"),
                "date": r.get("created_at") or r.get("date"),
            }

        if isinstance(r, (tuple, list)):
            return {
                "role": r[0] if len(r) > 0 else None,
                "content": r[1] if len(r) > 1 else None,
                "date": r[2] if len(r) > 2 else None,
            }

        return {"role": None, "content": None, "date": None}

    # ---- GRAPH ----
    def _build_graph(self):

        self.graph.add_node("init_node", self.init_node)
        self.graph.add_node("policy_router", self.policy_router_node)
        self.graph.add_node("chat_router", self.chat_router_node)

        self.graph.add_node("normal_chat", self.normal_chat_node)
        self.graph.add_node("memory_chat", self.memory_chat_node)
        self.graph.add_node("rag_chat", self.rag_chat_node)
        self.graph.add_node("memory_rag_chat", self.memory_rag_chat_node)

        self.graph.add_node("rejection_node", self.rejection_node)
        self.graph.add_node("output_node", self.output_node)

        self.graph.add_edge(START, "init_node")
        self.graph.add_edge("init_node", "policy_router")

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

    # ---- ROUTERS ----
    def _route_main(self, state: RAGState) -> str:
        return state.get("flag") or "REJECTION_FLAG"

    def _route_chat(self, state: RAGState) -> str:
        return state.get("chat_mode") or "NORMAL_FLAG"

    # ---- INIT NODE ----
    async def init_node(self, state: RAGState) -> RAGState:
        logger.info("[ENTER_NODE] init_node")

        try:
            if hasattr(self.semantic_memory, "init"):
                await self.semantic_memory.init()

            if hasattr(self.user_facts_memory, "load"):
                await self.user_facts_memory.load(user_id="1")

            if hasattr(self.transactions_memory, "warmup"):
                await self.transactions_memory.warmup(user_id="1")

            if hasattr(self.book_retriever, "init"):
                await self.book_retriever.init()

        except Exception as e:
            logger.exception(f"[INIT_NODE] failed | error={e}")

        return state.copy()

    # ---- POLICY ROUTER ----
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

    # ---- CHAT ROUTER ----
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

    # ---- MEMORY CHAT ----
    async def memory_chat_node(self, state: RAGState) -> RAGState:
        last_messages_raw = await self.semantic_memory.get_stm(user_id="1", limit=10)
        
        print(f"\n\n========> RAW LAST MESSAGES: {last_messages_raw} <=========\n\n")

        # STRICT projection only
        last_messages = [
            {
                "role": r[2] if len(r) > 2 else None,
                "content": r[3] if len(r) > 3 else None,
                "date": r[5] if len(r) > 5 else None,
            }
            for r in (last_messages_raw or [])
            if isinstance(r, (tuple, list))
        ]

        semantic_messages_raw = await self.semantic_memory.hybrid_search(
            user_id="1",
            query=state["user_query"],
            embedding=await self.embedder.embed(state["user_query"]),
            limit=20
        )

        semantic_messages = [
            {
                "role": r.get("role"),
                "content": r.get("content"),
                "date": r.get("created_at"),
            }
            for r in (semantic_messages_raw or [])
            if isinstance(r, dict)
        ]
        
        print(f"\n\n========> SEMANTIC MESSAGES: {semantic_messages} <=========\n\n")
        print(f"\n\n========> LAST MESSAGES: {last_messages} <=========\n\n")

        all_messages = last_messages + semantic_messages

        result = await self.safe_generator.run(
            prompt_file_name="chat_memory",
            content=state["user_query"],
            past_conversation=all_messages,
            temperature=0.0,
        )

        response = (
            result.get("data", {}).get("response")
            if isinstance(result.get("data"), dict)
            else None
        )

        state["chat_response"] = response
        return state.copy()

    # ---- RAG NODE (UNCHANGED) ----
    async def rag_chat_node(self, state: RAGState) -> RAGState:
        raw_docs = await self.book_retriever.search(state["user_query"], limit=5)

        docs = [{"content": d.get("summary") or d.get("content")} for d in (raw_docs or [])]

        result = await self.safe_generator.run(
            prompt_file_name="chat_rag",
            content=state["user_query"],
            chunks=docs,
            temperature=0.0,
        )

        response = (
            result.get("data", {}).get("response")
            if isinstance(result.get("data"), dict)
            else None
        )

        state["chat_response"] = response
        return state.copy()

    # ---- FIXED MEMORY+RAG ----
    async def memory_rag_chat_node(self, state: RAGState) -> RAGState:
        last_messages_raw = await self.semantic_memory.get_stm(user_id="1", limit=10)

        last_messages = [
            {
                "role": r[2] if len(r) > 2 else None,
                "content": r[3] if len(r) > 3 else None,
                "date": r[5] if len(r) > 5 else None,
            }
            for r in (last_messages_raw or [])
            if isinstance(r, (tuple, list))
        ]

        raw_docs = await self.book_retriever.search(state["user_query"], limit=5)

        docs = [{"content": d.get("summary") or d.get("content")} for d in (raw_docs or [])]

        result = await self.safe_generator.run(
            prompt_file_name="chat_memory_rag",
            content=state["user_query"],
            past_conversation=last_messages,
            chunks=docs,
            temperature=0.0,
        )

        response = (
            result.get("data", {}).get("response")
            if isinstance(result.get("data"), dict)
            else None
        )

        state["chat_response"] = response
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