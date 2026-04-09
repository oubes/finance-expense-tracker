# ---- Imports ----
from typing import TypedDict, Any
import logging
import asyncio
from langgraph.graph import StateGraph, START, END


# ---- Logger ----
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ---- State ----
class PipelineState(TypedDict):
    queries: list[dict] | None
    augmentation_messages: list[dict] | None
    generation_outputs: list[dict] | None
    extracted_outputs: list[dict] | None
    validated_outputs: list[dict] | None
    final_output: list[dict] | None


# ---- Pipeline ----
class AugGenPipeline:

    def __init__(
        self,
        msg_builder: Any,
        generator: Any,
        extractor: Any,
        validator: Any
    ) -> None:
        self.msg_builder = msg_builder
        self.generator = generator
        self.extractor = extractor
        self.validator = validator

        self.graph = StateGraph(PipelineState)
        self._build_graph()

    # ---- Graph ----
    def _build_graph(self) -> None:

        self.graph.add_node("augmentation_msg_builder", self.augmentation_msg_builder_node)
        self.graph.add_node("generation", self.generation_node)
        self.graph.add_node("extraction", self.extraction_node)
        self.graph.add_node("validation", self.validation_node)

        self.graph.add_edge(START, "augmentation_msg_builder")
        self.graph.add_edge("augmentation_msg_builder", "generation")
        self.graph.add_edge("generation", "extraction")
        self.graph.add_edge("extraction", "validation")
        self.graph.add_edge("validation", END)

        self.compiled = self.graph.compile()

    # ---- Nodes ----

    async def augmentation_msg_builder_node(self, state: PipelineState) -> PipelineState:

        if not state["queries"]:
            return state

        inputs: list[dict[str, Any]] = state["queries"]

        messages = await self.msg_builder.build_batch_async(
            prompt_file_name="aug_gen",
            inputs=inputs
        )

        state["augmentation_messages"] = messages
        return state

    async def generation_node(self, state: PipelineState) -> PipelineState:

        if not state["augmentation_messages"]:
            return state

        loop = asyncio.get_running_loop()

        tasks = [
            loop.run_in_executor(None, self.generator.generate, msg["data"])
            for msg in state["augmentation_messages"]
        ]

        results = await asyncio.gather(*tasks)

        state["generation_outputs"] = [
            {"id": state["augmentation_messages"][i].get("id"), "data": results[i]}
            for i in range(len(results))
        ]

        return state

    async def extraction_node(self, state: PipelineState) -> PipelineState:

        if not state["generation_outputs"]:
            return state

        extracted = await self.extractor.extract_batch(
            [r["data"] for r in state["generation_outputs"]]
        )

        state["extracted_outputs"] = [
            {
                "id": state["generation_outputs"][i]["id"],
                "data": extracted[i]
            }
            for i in range(len(extracted))
        ]

        return state

    def validation_node(self, state: PipelineState) -> PipelineState:

        if not state["extracted_outputs"]:
            return state

        validated = self.validator.validate_batch(
            [e["data"] for e in state["extracted_outputs"]]
        )

        state["validated_outputs"] = [
            {
                "id": state["extracted_outputs"][i]["id"],
                "data": validated[i]["data"],
                "state": validated[i]["state"]
            }
            for i in range(len(validated))
        ]

        state["final_output"] = [
            v for v in state["validated_outputs"] if v["state"]
        ]

        return state

    # ---- Runner ----
    async def run(self, queries: list[dict[str, Any]]) -> PipelineState:

        initial_state: PipelineState = {
            "queries": queries,
            "augmentation_messages": None,
            "generation_outputs": None,
            "extracted_outputs": None,
            "validated_outputs": None,
            "final_output": None
        }

        return await self.compiled.ainvoke(initial_state)  # type: ignore
    
    