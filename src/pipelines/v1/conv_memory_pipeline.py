# ---- Imports ----
import asyncio
import logging
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from src.shared.graph_builder import GraphSaver


# ---- Logger ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---- State ----
class MemoryState(TypedDict):
    conversation_memory_entry: dict
    session_id: str | None
    user_id: str | None

    conversation_memory_initialized: bool | None
    conversation_memory_stored: bool | None


# ----------- MemoryFlow -----------

class MemoryFlow:

    def __init__(self, conversation_ops):
        self.ops = conversation_ops
        self.graph = self._build()

    async def _init(self, state: MemoryState):
        logger.info("[MemoryFlow] init")

        ok = await self.ops.init()

        return {
            **state,
            "conversation_memory_initialized": ok
        }

    async def _store(self, state: MemoryState):
        logger.info("[MemoryFlow] store conversation memory")

        payload = state["conversation_memory_entry"]

        record = (
            state.get("session_id"),
            state.get("user_id"),
            payload.get("role"),
            payload.get("content"),
        )

        ok = await self.ops.add(record)

        return {
            **state,
            "conversation_memory_stored": ok
        }

    def _build(self):
        g = StateGraph(MemoryState)

        g.add_node("initialize_conversational_memory", self._init)
        g.add_node("store_conversational_memory_entry", self._store)

        g.add_edge(START, "initialize_conversational_memory")
        g.add_edge("initialize_conversational_memory", "store_conversational_memory_entry")
        g.add_edge("store_conversational_memory_entry", END)

        return g.compile()

    async def run(self, payload: dict, session_id: str | None = None, user_id: str | None = None):
        return await self.graph.ainvoke({
            "conversation_memory_entry": payload,
            "session_id": session_id,
            "user_id": user_id,
            "conversation_memory_initialized": None,
            "conversation_memory_stored": None
        })


# ----------- Entry Point -----------

class MemorySystem:

    def __init__(self, conversation_ops):
        self.flow = MemoryFlow(conversation_ops)
        self.graph_saver = GraphSaver("memory_flow.png")

    async def run(self, payload: dict, session_id: str | None = None, user_id: str | None = None):
        self.graph_saver.save(self.flow.graph)
        return await self.flow.run(payload, session_id, user_id)