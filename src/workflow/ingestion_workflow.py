# ---- Imports ----
from typing import TypedDict
import logging

from langgraph.graph import StateGraph, START, END
from src.shared.graph_builder import GraphSaver
from src.core.schemas.workflow.ingestion_schema import WorkflowOutput

logger = logging.getLogger(__name__)


# ---- State ----
class IngestionState(TypedDict):
    workflow_output: list[WorkflowOutput] | None
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

        logger.info("Initializing IngestionWorkflow")

        self.graph = StateGraph(IngestionState)
        self._build_graph()
        self.graph_saver = GraphSaver("ingestion_workflow.png")

    # ---- Graph ----
    def _build_graph(self) -> None:
        logger.info("Building workflow graph")

        self.graph.add_node("init_table", self.init_table_node)
        self.graph.add_node("check_empty", self.check_empty_node)

        self.graph.add_node("run_pipeline", self.run_pipeline_node)
        self.graph.add_node("run_pipeline_overwrite", self.run_pipeline_overwrite_node)

        self.graph.add_node("upsert_only", self.upsert_only_node)
        self.graph.add_node("delete_and_upsert", self.delete_and_upsert_node)

        self.graph.add_node("decide_overwrite", self.decide_overwrite_node)

        self.graph.add_edge(START, "init_table")
        self.graph.add_edge("init_table", "check_empty")

        # ---- Routing from empty check ----
        self.graph.add_conditional_edges(
            "check_empty",
            self.route_empty,
            {
                "empty": "run_pipeline",
                "not_empty": "decide_overwrite",
            },
        )

        # ---- Decide overwrite ----
        self.graph.add_conditional_edges(
            "decide_overwrite",
            self.route_overwrite,
            {
                "true": "run_pipeline_overwrite",
                "false": END,
            },
        )

        # ---- Pipeline (empty table OR overwrite true) ----
        self.graph.add_edge("run_pipeline", "upsert_only")
        self.graph.add_edge("run_pipeline_overwrite", "delete_and_upsert")

        self.graph.add_edge("upsert_only", END)
        self.graph.add_edge("delete_and_upsert", END)

        self.compiled = self.graph.compile()

        logger.info("Workflow graph compiled successfully")

    # ---- Routing ----
    def route_empty(self, state: IngestionState) -> str:
        decision = "empty" if state.get("table_empty") else "not_empty"
        logger.info(f"Routing (route_empty): {decision}")
        return decision

    def route_overwrite(self, state: IngestionState) -> str:
        decision = "true" if state.get("overwrite") else "false"
        logger.info(f"Routing (route_overwrite): {decision}")
        return decision

    # ---- Nodes ----

    async def init_table_node(self, state: IngestionState) -> IngestionState:
        logger.info("Node: init_table started")
        await self.init_table_fn()
        logger.info("Node: init_table completed")
        return state

    async def check_empty_node(self, state: IngestionState) -> IngestionState:
        logger.info("Node: check_empty started")
        count = await self.count_fn()
        state["table_empty"] = count == 0
        logger.info(f"Table empty: {state['table_empty']} (count={count})")
        return state

    # ---- Shared pipeline logic ----
    async def _execute_pipeline(self) -> list[WorkflowOutput]:
        result = await self.pipeline.run()
        raw_output = result.get("final_pipeline_output") or []

        logger.info(f"Pipeline returned {len(raw_output)} records")

        workflow_outputs: list[WorkflowOutput] = []

        for idx, item in enumerate(raw_output):
            if hasattr(item, "model_dump"):
                item_dict = item.model_dump()
            elif isinstance(item, dict):
                item_dict = item
            else:
                logger.error(f"Invalid pipeline item at index {idx}: {type(item)}")
                raise TypeError(f"Unsupported pipeline output type: {type(item)}")

            workflow_outputs.append(WorkflowOutput(**item_dict))

        return workflow_outputs

    async def run_pipeline_node(self, state: IngestionState) -> IngestionState:
        logger.info("Node: run_pipeline started")

        workflow_outputs = await self._execute_pipeline()
        state["workflow_output"] = workflow_outputs

        logger.info(f"Converted pipeline output: {len(workflow_outputs)} records")
        return state

    async def run_pipeline_overwrite_node(self, state: IngestionState) -> IngestionState:
        logger.info("Node: run_pipeline_overwrite started")

        workflow_outputs = await self._execute_pipeline()
        state["workflow_output"] = workflow_outputs

        logger.info(f"Overwrite pipeline output: {len(workflow_outputs)} records")
        return state

    async def upsert_only_node(self, state: IngestionState) -> IngestionState:
        logger.info("Node: upsert_only started")

        records = state.get("workflow_output") or []

        if not records:
            logger.warning("No records to upsert")
            return state

        try:
            await self.upsert_fn(records=records)
            logger.info(f"Upsert completed: records={len(records)}")

        except Exception as e:
            logger.exception(f"upsert_only_node failed: {e}")
            raise

        return state

    async def delete_and_upsert_node(self, state: IngestionState) -> IngestionState:
        logger.info("Node: delete_and_upsert started")

        try:
            await self.delete_fn()
            logger.info("Existing data deleted")

            records = state.get("workflow_output") or []

            if not records:
                logger.warning("No records to upsert after delete")
                return state

            await self.upsert_fn(records=records)

            logger.info(f"Delete + Upsert completed: records={len(records)}")

        except Exception as e:
            logger.exception(f"delete_and_upsert_node failed: {e}")
            raise

        return state

    async def decide_overwrite_node(self, state: IngestionState) -> IngestionState:
        logger.info(f"Deciding overwrite: {state.get('overwrite')}")
        return state

    # ---- Runner ----
    async def run(self, overwrite: bool = True) -> IngestionState:
        logger.info(f"Workflow run started (overwrite={overwrite})")

        initial_state: IngestionState = {
            "workflow_output": None,
            "table_empty": None,
            "overwrite": overwrite,
        }

        try:
            self.graph_saver.save(self.compiled)
            result = await self.compiled.ainvoke(initial_state)  # type: ignore

            logger.info("Workflow completed")

            return result  # type: ignore

        except Exception as e:
            logger.exception(f"Workflow execution failed: {e}")
            raise