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
    messages: list[dict] | None
    llm_raw: str | None
    parsed_output: dict | None
    validated_output: dict | None
    flag: str | None

    retrieved_docs: list[dict] | None
    chunks: str | None
    final_output: Any | None


# ---- RAG Workflow ----
class RAGWorkflow:

    # ---- Constructor ----
    def __init__(
        self,
        msg_builder,
        generator,
        extractor,
        validator,
        aug_gen_pipeline,
        hybrid_retriever,
    ):
        self.msg_builder = msg_builder
        self.generator = generator
        self.extractor = extractor
        self.validator = validator
        self.aug_gen_pipeline = aug_gen_pipeline
        self.hybrid_retriever = hybrid_retriever

        self.graph = StateGraph(RAGState)
        self._build_graph()

        self.compiled = self.graph.compile()
        self.graph_saver = GraphSaver("rag_workflow.png")

    # ---- Graph Builder ----
    def _build_graph(self) -> None:

        # ---- Entry Flow ----
        self.graph.add_node("build_entry_msg", self.build_entry_msg_node)
        self.graph.add_node("generate_entry", self.generate_node)
        self.graph.add_node("extract_entry", self.extract_node)
        self.graph.add_node("validate_entry", self.validate_node)

        # ---- Branches ----
        self.graph.add_node("ask_more_info_msg", self.ask_more_info_msg_node)
        self.graph.add_node("reject_msg", self.reject_msg_node)

        # ---- Retrieval Flow ----
        self.graph.add_node("retrieve", self.retrieve_node)
        self.graph.add_node("extract_chunks", self.extract_chunks_node)
        self.graph.add_node("augment_generate_node", self.augment_generate_pipeline_node)

        # ---- Edges ----
        self.graph.add_edge(START, "build_entry_msg")
        self.graph.add_edge("build_entry_msg", "generate_entry")
        self.graph.add_edge("generate_entry", "extract_entry")
        self.graph.add_edge("extract_entry", "validate_entry")

        # ---- Conditional Routing ----
        self.graph.add_conditional_edges(
            "validate_entry",
            self._route_flag,
            {
                "SUCCESS": "retrieve",
                "ASK_FOR_MORE_INFO": "ask_more_info_msg",
                "REJECTED": "reject_msg",
            },
        )

        # ---- Ask More Info Flow ----
        self.graph.add_edge("ask_more_info_msg", "generate_entry")
        self.graph.add_edge("generate_entry", "extract_entry")
        self.graph.add_edge("extract_entry", "validate_entry")

        # ---- Reject Flow ----
        self.graph.add_edge("reject_msg", "generate_entry")

        # ---- Retrieval Flow ----
        self.graph.add_edge("retrieve", "extract_chunks")
        self.graph.add_edge("extract_chunks", "augment_generate_node")
        self.graph.add_edge("augment_generate_node", END)

    # ---- Router ----
    def _route_flag(self, state: RAGState) -> str:
        return state.get("flag") or "REJECTED"

    # ---- Node: Build Entry Msg ----
    async def build_entry_msg_node(self, state: RAGState) -> RAGState:

        result = await self.msg_builder.build_async(
            prompt_file_name="entry_router",
            user_question=state["question"],  # TODO: fill
            context="",  # TODO: fill
        )

        state["messages"] = result.get("data")

        return state

    # ---- Node: Ask More Info Msg ----
    async def ask_more_info_msg_node(self, state: RAGState) -> RAGState:

        result = await self.msg_builder.build_async(
            prompt_file_name="more_info_request",
            user_question=state["question"],  # TODO: fill
            context="",  # TODO: fill
        )

        state["messages"] = result.get("data")

        return state

    # ---- Node: Reject Msg ----
    async def reject_msg_node(self, state: RAGState) -> RAGState:

        result = await self.msg_builder.build_async(
            prompt_file_name="rejection_response",
            user_question=state["question"],  # TODO: fill
            context="",  # TODO: fill
        )

        state["messages"] = result.get("data")

        return state

    # ---- Node: Generate ----
    async def generate_node(self, state: RAGState) -> RAGState:

        response = await self.generator.generate(  # type: ignore
            messages=state.get("messages") or []
        )

        state["llm_raw"] = response

        return state

    # ---- Node: Extract ----
    async def extract_node(self, state: RAGState) -> RAGState:

        parsed = await self.extractor.extract_one(
            state.get("llm_raw") or ""
        )

        state["parsed_output"] = parsed

        return state

    # ---- Node: Validate ----
    async def validate_node(self, state: RAGState) -> RAGState:

        validated = self.validator.validate_one(
            state.get("parsed_output") or {},
            required_keys={"flag"},  # TODO: extend
            allowed_flags={"SUCCESS", "ASK_FOR_MORE_INFO", "REJECTED"},
        )

        state["validated_output"] = validated

        if validated.get("state"):
            data = validated.get("data") or {}
            state["flag"] = data.get("flag")

        return state

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
    async def augment_generate_pipeline_node(self, state: RAGState) -> RAGState:

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
            "messages": None,
            "llm_raw": None,
            "parsed_output": None,
            "validated_output": None,
            "flag": None,
            "retrieved_docs": None,
            "chunks": None,
            "final_output": None,
        }

        self.graph_saver.save(self.compiled)

        return await self.compiled.ainvoke(initial_state)  # type: ignore