# ---- Imports ----
from typing import TypedDict
import logging

from pydantic import ValidationError

from langgraph.graph import StateGraph, START, END
from src.shared.graph_builder import GraphSaver
from src.core.schemas.workflow.ingestion_schema import WorkflowOutput
from src.core.schemas.pipeline.ingestion_schema import PipelineOutput

logger = logging.getLogger(__name__)


# ---- State ----
class IngestionState(TypedDict):
    raw_output: list[object] | None
    normalized_output: list[dict] | None
    validated_output: list[WorkflowOutput] | None
    table_empty: bool | None
    overwrite: bool


# ---- Workflow ----
class IngestionWorkflow:

    def __init__(
        self,
        pipeline,
        db_client,
        init_table_fn,
        upsert_fn,
        delete_fn,
        count_fn,
    ) -> None:

        self.pipeline = pipeline
        self.db_client = db_client
        self.init_table_fn = init_table_fn
        self.upsert_fn = upsert_fn
        self.delete_fn = delete_fn
        self.count_fn = count_fn

        self.graph = StateGraph(IngestionState)
        self._build_graph()
        self.graph_saver = GraphSaver("ingestion_workflow.png")

    # ---- Graph ----
    def _build_graph(self) -> None:

        self.graph.add_node("init_table", self.init_table_node)
        self.graph.add_node("check_empty", self.check_empty_node)

        self.graph.add_node("run_pipeline", self.run_pipeline_node)
        self.graph.add_node("normalize_output", self.normalize_output_node)
        self.graph.add_node("validate_output", self.validate_output_node)
        self.graph.add_node("upsert_output", self.upsert_output_node)

        self.graph.add_node("delete_data", self.delete_data_node)
        self.graph.add_node("decide_overwrite", self.decide_overwrite_node)

        self.graph.add_edge(START, "init_table")
        self.graph.add_edge("init_table", "check_empty")

        # ---- Routing ----
        self.graph.add_conditional_edges(
            "check_empty",
            self.route_empty,
            {
                "empty": "run_pipeline",
                "not_empty": "decide_overwrite",
            },
        )

        self.graph.add_conditional_edges(
            "decide_overwrite",
            self.route_overwrite,
            {
                "true": "delete_data",
                "false": END,
            },
        )

        # ---- Flow ----
        self.graph.add_edge("delete_data", "run_pipeline")

        self.graph.add_edge("run_pipeline", "normalize_output")
        self.graph.add_edge("normalize_output", "validate_output")
        self.graph.add_edge("validate_output", "upsert_output")

        self.graph.add_edge("upsert_output", END)

        self.compiled = self.graph.compile()

    # ---- Routing ----
    def route_empty(self, state: IngestionState) -> str:
        return "empty" if state.get("table_empty") else "not_empty"

    def route_overwrite(self, state: IngestionState) -> str:
        return "true" if state.get("overwrite") else "false"

    # ---- Nodes ----

    async def init_table_node(self, state: IngestionState) -> IngestionState:
        await self.init_table_fn()
        return state

    async def check_empty_node(self, state: IngestionState) -> IngestionState:
        count = await self.count_fn()
        state["table_empty"] = count == 0
        return state

    # ---- Delete Node ----
    async def delete_data_node(self, state: IngestionState) -> IngestionState:
        logger.info("Deleting existing data (overwrite=True)")
        await self.delete_fn()
        return state

    # ---- Node 1: Run Pipeline ----
    async def run_pipeline_node(self, state: IngestionState) -> IngestionState:

        result = await self.pipeline.run()
        raw_output = result.get("final_pipeline_output", [])

        if not isinstance(raw_output, list):
            raise TypeError("Pipeline output must be list")

        logger.info(f"Pipeline returned {len(raw_output)} records")

        state["raw_output"] = raw_output
        return state

    # ---- Node 2: Normalize ----
    async def normalize_output_node(self, state: IngestionState) -> IngestionState:

        raw = state.get("raw_output") or []
        normalized: list[dict] = []

        for idx, item in enumerate(raw):

            if hasattr(item, "model_dump"):
                item_dict = item.model_dump() # type: ignore

            elif isinstance(item, dict):
                item_dict = item

            else:
                raise TypeError(f"Unsupported type at index {idx}: {type(item)}")

            normalized.append(item_dict)

        state["normalized_output"] = normalized
        return state

    # ---- Node 3: Validate ----
# ---- Node 3: Validate ----
    async def validate_output_node(self, state: IngestionState) -> IngestionState:

        normalized = state.get("normalized_output") or []

        validated: list[WorkflowOutput] = []
        pipeline_validated: list[PipelineOutput] = []

        for idx, item in enumerate(normalized):

            try:
                pipeline_obj = PipelineOutput.model_validate(item)
                pipeline_validated.append(pipeline_obj)

                workflow_obj = WorkflowOutput(
                    **pipeline_obj.model_dump()
                )

                validated.append(workflow_obj)

            except ValidationError as ve:
                logger.error(
                    f"[ValidationError] index={idx} | does not match PipelineOutput | {ve}"
                )

            except Exception as e:
                logger.error(
                    f"[UnexpectedError] index={idx} | {type(e)} | {e}"
                )

        state["validated_output"] = validated

        logger.info(
            f"Validation completed: {len(validated)}/{len(normalized)} records passed PipelineOutput schema"
        )

        return state

    # ---- Node 4: Upsert ----
    async def upsert_output_node(self, state: IngestionState) -> IngestionState:

        records = state.get("validated_output") or []

        if not records:
            logger.warning("No valid records to upsert")
            return state

        await self.upsert_fn(records=records)

        logger.info(f"Upsert completed: {len(records)} records")

        return state

    async def decide_overwrite_node(self, state: IngestionState) -> IngestionState:
        return state

    # ---- Runner ----
    async def run(self, overwrite: bool = True) -> IngestionState:

        initial_state: IngestionState = {
            "raw_output": None,
            "normalized_output": None,
            "validated_output": None,
            "table_empty": None,
            "overwrite": overwrite,
        }

        self.graph_saver.save(self.compiled)
        return await self.compiled.ainvoke(initial_state)  # type: ignore