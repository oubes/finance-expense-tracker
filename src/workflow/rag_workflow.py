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
    flag: str | None

    messages: list[dict] | None
    parsed_output: dict | None

    retrieved_docs: list[dict] | None
    chunks: str | None
    final_output: Any | None


# ---- RAG Workflow ----
class RAGWorkflow:

    # ---- Constructor ----
    def __init__(
        self,
        safe_generator,
        aug_gen_pipeline,
        hybrid_retriever,
    ):
        self.safe_generator = safe_generator
        self.aug_gen_pipeline = aug_gen_pipeline
        self.hybrid_retriever = hybrid_retriever

        self.graph = StateGraph(RAGState)
        self._build_graph()

        self.compiled = self.graph.compile()
        self.graph_saver = GraphSaver("rag_workflow.png")

    # ---- Graph Builder ----
    def _build_graph(self) -> None:

        # ---- Core Nodes ----
        self.graph.add_node("policy_router", self.policy_router_node)

        # ---- Generation Nodes ----
        self.graph.add_node("prepare_rejection_msg", self.prepare_rejection_msg_node)
        self.graph.add_node("prepare_asking_msg", self.prepare_asking_msg_node)
        self.graph.add_node("chat_msg_gen", self.chat_msg_node)
        self.graph.add_node("mem_msg_gen", self.mem_msg_node)
        self.graph.add_node("rag_msg_gen", self.rag_msg_node)
        self.graph.add_node("mem_and_rag_gen", self.mem_and_rag_msg_node)

        # ---- Data Nodes ----
        self.graph.add_node("pull_mem", self.pull_mem_node)
        self.graph.add_node("pull_mem_and_ret", self.pull_mem_and_ret_node)

        # ---- Edges ----
        self.graph.add_edge(START, "policy_router")

        # ---- Routing ----
        self.graph.add_conditional_edges(
            "policy_router",
            self._route_flag,
            {
                "rejected": "prepare_rejection_msg",
                "ask_for_more_info": "prepare_asking_msg",
                "chat": "chat_msg_gen",
                "mem": "pull_mem",
                "rag": "rag_msg_gen",
                "mem_and_rag": "pull_mem_and_ret",
            },
        )

        # ---- Simple Paths ----
        self.graph.add_edge("prepare_rejection_msg", END)
        self.graph.add_edge("prepare_asking_msg", END)
        self.graph.add_edge("chat_msg_gen", END)
        self.graph.add_edge("rag_msg_gen", END)

        # ---- Memory Path ----
        self.graph.add_edge("pull_mem", "mem_msg_gen")
        self.graph.add_edge("mem_msg_gen", END)

        # ---- Mem + RAG Path ----
        self.graph.add_edge("pull_mem_and_ret", "mem_and_rag_gen")
        self.graph.add_edge("mem_and_rag_gen", END)

    # ---- Router ----
    def _route_flag(self, state: RAGState) -> str:
        return state.get("flag") or "rejected"

    # ---- Node: Policy Router ----
    async def policy_router_node(self, state: RAGState) -> RAGState:

        result = await self.safe_generator.run(
            prompt_file_name="entry_router",
            user_question=state["question"],
            context="",
        )

        state["parsed_output"] = result

        if result.get("state"):
            state["flag"] = result["data"].get("flag")

        return state

    # ---- Node: Rejection ----
    async def prepare_rejection_msg_node(self, state: RAGState) -> RAGState:

        result = await self.safe_generator.run(
            prompt_file_name="rejection_response",
            user_question=state["question"],
            context="",
        )

        state["final_output"] = result
        return state

    # ---- Node: Ask ----
    async def prepare_asking_msg_node(self, state: RAGState) -> RAGState:

        result = await self.safe_generator.run(
            prompt_file_name="more_info_request",
            user_question=state["question"],
            context="",
        )

        state["final_output"] = result
        return state

    # ---- Node: Chat ----
    async def chat_msg_node(self, state: RAGState) -> RAGState:

        result = await self.safe_generator.run(
            prompt_file_name="chat_response",
            user_question=state["question"],
            context="",
        )

        state["final_output"] = result
        return state

    # ---- Node: Pull Memory ----
    async def pull_mem_node(self, state: RAGState) -> RAGState:

        # TODO: replace with real memory retrieval
        state["chunks"] = "memory context"

        return state

    # ---- Node: Memory Msg ----
    async def mem_msg_node(self, state: RAGState) -> RAGState:

        result = await self.safe_generator.run(
            prompt_file_name="memory_response",
            user_question=state["question"],
            context=state.get("chunks") or "",
        )

        state["final_output"] = result
        return state

    # ---- Node: RAG Msg ----
    async def rag_msg_node(self, state: RAGState) -> RAGState:

        result = await self.aug_gen_pipeline.run(
            queries=[
                {
                    "user_question": state["question"],
                    "chunks": "",
                }
            ]
        )

        state["final_output"] = result
        return state

    # ---- Node: Pull Mem + Retrieve ----
    async def pull_mem_and_ret_node(self, state: RAGState) -> RAGState:

        docs = await self.hybrid_retriever.search(
            input_query=state["question"]
        )

        chunks = " ".join(
            (d.get("content") or "").strip()
            for d in docs
            if isinstance(d, dict)
        )

        state["chunks"] = chunks + " memory context"

        return state

    # ---- Node: Mem + RAG Msg ----
    async def mem_and_rag_msg_node(self, state: RAGState) -> RAGState:

        result = await self.safe_generator.run(
            prompt_file_name="mem_and_rag_response",
            user_question=state["question"],
            context=state.get("chunks") or "",
        )

        state["final_output"] = result
        return state

    # ---- Runner ----
    async def run(self, question: str):

        initial_state: RAGState = {
            "question": question,
            "flag": None,
            "messages": None,
            "parsed_output": None,
            "retrieved_docs": None,
            "chunks": None,
            "final_output": None,
        }

        self.graph_saver.save(self.compiled)

        return await self.compiled.ainvoke(initial_state)  # type: ignore