# ---- Imports ----
import logging
from typing import TypedDict, Literal

from langgraph.graph import StateGraph, START, END
from src.shared.graph_builder import GraphSaver

logger = logging.getLogger(__name__)


class MemoryState(TypedDict):
    user_input: str
    user_id: str | None

    role: Literal["user", "ai"] | None

    intent: Literal[
        "transactions",
        "facts",
        "none"
    ] | None

    extracted_transactions: dict | None
    extracted_facts: dict | None
    extracted_semantic_memory: dict | None

    response_ready: bool | None


class MemoryPipeline:

    def __init__(
        self,
        transactions_ops,
        semantic_memory_ops,
        user_facts_ops,
        safe_generator,
        embedder
    ):
        self.tx_ops = transactions_ops
        self.semantic_ops = semantic_memory_ops
        self.facts_ops = user_facts_ops
        self.embedder = embedder
        self.safe_gen = safe_generator

        self.graph = self._build()

        self.graph_saver = GraphSaver("memory_pipeline.png")
        self._save_graph()

    # ---------------- GRAPH SAVE ----------------
    def _save_graph(self):
        try:
            self.graph_saver.save(self.graph)
            logger.info("[GraphSaver] graph saved successfully")
        except Exception as e:
            logger.exception(f"[GraphSaver] graph save failed: {e}")

    # ---------------- INIT GUARD ----------------
    async def _ensure_init(self):
        try:
            await self.tx_ops.init()
            await self.semantic_ops.init()
            await self.facts_ops.init()
        except Exception as e:
            logger.exception(f"[INIT GUARD FAILED] {e}")

    # ---------------- CLEAN ----------------
    def _clean(self, v):
        if v in ("null", "None", "", None):
            return None
        return int(v) if isinstance(v, str) and v.isdigit() else v

    # ---------------- SEMANTIC (USER) ----------------
    async def _semantic_memory(self, state: MemoryState):
        text = state["user_input"]
        user_id = state["user_id"]

        try:
            embedding = await self.embedder.embed(text)
            embedding = embedding.tolist() if hasattr(embedding, "tolist") else embedding

            await self.semantic_ops.add_message(
                user_id=user_id,
                role="user",
                content=text,
                embedding=embedding
            )

            return {
                **state,
                "extracted_semantic_memory": {
                    "role": "user",
                    "content": text
                }
            }

        except Exception as e:
            logger.exception(e)
            return {**state, "response_ready": False}

    # ---------------- SEMANTIC (AI PATH) ----------------
    async def _ai_semantic_memory(self, state: MemoryState):
        text = state["user_input"]
        user_id = state["user_id"]

        try:
            embedding = await self.embedder.embed(text)
            embedding = embedding.tolist() if hasattr(embedding, "tolist") else embedding

            await self.semantic_ops.add_message(
                user_id=user_id,
                role="ai",
                content=text,
                embedding=embedding
            )

            return {
                **state,
                "extracted_semantic_memory": {
                    "role": "ai",
                    "content": text
                },
                "response_ready": True
            }

        except Exception as e:
            logger.exception(e)
            return {**state, "response_ready": False}

    # ---------------- INTENT ----------------
    async def _detect_intent(self, state: MemoryState):
        try:
            result = await self.safe_gen.run(
                prompt_file_name="memory_intent_router",
                user_input=state["user_input"],
                required_keys={"transactions", "facts"},
                temperature=0.0,
            )

            if not result.get("state"):
                return {**state, "intent": "none"}

            d = result["data"]

            intent = (
                "transactions" if d.get("transactions") == "true"
                else "facts" if d.get("facts") == "true"
                else "none"
            )

            return {**state, "intent": intent}

        except Exception as e:
            logger.exception(e)
            return {**state, "intent": "none"}

    # ---------------- TRANSACTIONS ----------------
    async def _transactions(self, state: MemoryState):
        try:
            if not await self.tx_ops.init():
                return {**state, "response_ready": False}

            result = await self.safe_gen.run(
                prompt_file_name="tx_memory_extractor",
                user_input=state["user_input"],
                required_keys={
                    "product", "category", "amount",
                    "quantity", "currency", "note"
                },
                temperature=0.0,
            )

            if not result.get("state"):
                return {**state, "response_ready": False}

            d = result["data"]

            extracted = {
                "product": self._clean(d.get("product")),
                "category": self._clean(d.get("category")),
                "amount": self._clean(d.get("amount")),
                "quantity": self._clean(d.get("quantity")),
                "currency": self._clean(d.get("currency")),
                "note": self._clean(d.get("note")),
                "raw_input": state["user_input"]
            }

            embedding = await self.embedder.embed(state["user_input"])
            embedding = embedding.tolist() if hasattr(embedding, "tolist") else embedding

            ok = await self.tx_ops.log_event((
                state["user_id"],
                extracted["product"],
                extracted["category"],
                extracted["amount"],
                extracted["quantity"],
                extracted["currency"],
                extracted["note"],
                extracted["raw_input"],
                embedding
            ))

            if not ok:
                return {**state, "response_ready": False}

            return {
                **state,
                "extracted_transactions": extracted,
                "response_ready": True
            }

        except Exception as e:
            logger.exception(e)
            return {**state, "response_ready": False}

    # ---------------- FACTS ----------------
    async def _facts(self, state: MemoryState):
        try:
            if not await self.facts_ops.init():
                return {**state, "response_ready": False}

            result = await self.safe_gen.run(
                prompt_file_name="user_facts_memory_extractor",
                user_input=state["user_input"],
                required_keys={
                    "income", "currency",
                    "rent", "food_expense",
                    "fixed_expenses", "disposable_income"
                },
                temperature=0.0,
            )

            if not result.get("state"):
                return {**state, "response_ready": False}

            d = result["data"]

            extracted = {
                "income": self._clean(d.get("income")),
                "currency": self._clean(d.get("currency")),
                "rent": self._clean(d.get("rent")),
                "food_expense": self._clean(d.get("food_expense")),
                "fixed_expenses": self._clean(d.get("fixed_expenses")),
                "disposable_income": self._clean(d.get("disposable_income")),
            }

            ok = await self.facts_ops.add((
                state["user_id"],
                extracted["income"],
                extracted["currency"],
                extracted["rent"],
                extracted["food_expense"],
                extracted["fixed_expenses"],
                extracted["disposable_income"],
            ))

            if not ok:
                return {**state, "response_ready": False}

            return {
                **state,
                "extracted_facts": extracted,
                "response_ready": True
            }

        except Exception as e:
            logger.exception(e)
            return {**state, "response_ready": False}

    # ---------------- BUILD GRAPH ----------------
    def _build(self):
        g = StateGraph(MemoryState)

        g.add_node("semantic_memory", self._semantic_memory)
        g.add_node("ai_semantic_memory", self._ai_semantic_memory)
        g.add_node("detect_intent", self._detect_intent)
        g.add_node("transactions", self._transactions)
        g.add_node("facts", self._facts)

        # ENTRY ROUTING (NO EXTRA NODE)
        g.add_conditional_edges(
            START,
            lambda s: s.get("role") or "user",
            {
                "user": "semantic_memory",
                "ai": "ai_semantic_memory",
            }
        )

        # USER FLOW
        g.add_edge("semantic_memory", "detect_intent")

        g.add_conditional_edges(
            "detect_intent",
            lambda s: s["intent"] or "none",
            {
                "transactions": "transactions",
                "facts": "facts",
                "none": END,
            }
        )

        g.add_edge("transactions", END)
        g.add_edge("facts", END)

        # AI FLOW
        g.add_edge("ai_semantic_memory", END)

        return g.compile()

    async def run(self, user_input: str, user_id: str, role: Literal["user", "ai"] = "user"):
        await self._ensure_init()

        return await self.graph.ainvoke({
            "user_input": user_input,
            "user_id": user_id,
            "role": role,
            "intent": None,
            "extracted_transactions": None,
            "extracted_facts": None,
            "extracted_semantic_memory": None,
            "response_ready": None
        })