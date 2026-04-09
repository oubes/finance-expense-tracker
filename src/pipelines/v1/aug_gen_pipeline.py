# ---- Imports ----
from typing import TypedDict, Any
import logging
import asyncio
from langgraph.graph import StateGraph, START, END
from src.shared.graph_builder import GraphSaver

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
        logger.info("[init] initializing pipeline components")

        self.msg_builder = msg_builder
        self.generator = generator
        self.extractor = extractor
        self.validator = validator

        self.graph = StateGraph(PipelineState)
        self._build_graph()

        logger.info("[init] pipeline initialized successfully")

    # ---- Graph ----
    def _build_graph(self) -> None:
        try:
            logger.info("[graph] building graph nodes")

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
            self.graph_saver = GraphSaver(filename="aug_gen_pipeline.png")

            logger.info("[graph] graph compiled and saver initialized")

        except Exception as e:
            logger.exception(f"[graph] graph build failed: {e}")
            raise

    # ---- Nodes ----

    async def augmentation_msg_builder_node(self, state: PipelineState) -> PipelineState:
        logger.info("[augmentation] start")

        try:
            if not state["queries"]:
                logger.info("[augmentation] skipped (no queries)")
                return state

            inputs: list[dict[str, Any]] = state["queries"]

            messages = await self.msg_builder.build_batch_async(
                prompt_file_name="aug_gen",
                inputs=inputs
            )

            state["augmentation_messages"] = messages

            logger.info("[augmentation] completed")

            return state

        except Exception as e:
            logger.exception(f"[augmentation] failed: {e}")
            raise

    async def generation_node(self, state: PipelineState) -> PipelineState:
        logger.info("[generation] start")

        try:
            if not state["augmentation_messages"]:
                logger.info("[generation] skipped (no messages)")
                return state

            tasks = [
                self.generator.generate(msg["data"], max_tokens=1024)
                for msg in state["augmentation_messages"]
            ]

            results = await asyncio.gather(*tasks)

            state["generation_outputs"] = [
                {
                    "id": state["augmentation_messages"][i].get("id"),
                    "data": results[i]
                }
                for i in range(len(results))
            ]

            logger.info("[generation] completed")

            return state

        except Exception as e:
            logger.exception(f"[generation] failed: {e}")
            raise

    async def extraction_node(self, state: PipelineState) -> PipelineState:
        logger.info("[extraction] start")

        try:
            if not state["generation_outputs"]:
                logger.info("[extraction] skipped (no generation outputs)")
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

            logger.info("[extraction] completed")

            return state

        except Exception as e:
            logger.exception(f"[extraction] failed: {e}")
            raise

    def validation_node(self, state: PipelineState) -> PipelineState:
        logger.info("[validation] start")

        try:
            if not state["extracted_outputs"]:
                logger.info("[validation] skipped (no extracted outputs)")
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

            logger.info("[validation] completed")

            return state

        except Exception as e:
            logger.exception(f"[validation] failed: {e}")
            raise

    # ---- Runner ----
    async def run(self, queries: list[dict[str, Any]]) -> PipelineState:
        logger.info("[run] pipeline execution started")

        try:
            initial_state: PipelineState = {
                "queries": queries,
                "augmentation_messages": None,
                "generation_outputs": None,
                "extracted_outputs": None,
                "validated_outputs": None,
                "final_output": None
            }

            logger.info("[run] saving graph visualization")
            self.graph_saver.save(self.compiled)

            result = await self.compiled.ainvoke(initial_state)  # type: ignore

            logger.info("[run] pipeline execution completed")

            return result # type: ignore

        except Exception as e:
            logger.exception(f"[run] pipeline execution failed: {e}")
            raise