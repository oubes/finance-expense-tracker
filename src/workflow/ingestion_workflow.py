# ---- Imports ----
from typing import TypedDict, Any
import logging

from langgraph.graph import StateGraph, START, END
from src.shared.graph_builder import GraphSaver
from src.core.schemas.pipeline.ingestion_schema import PipelineOutput

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ---- State ----
class IngestionState(TypedDict):
    pipeline_output: list[PipelineOutput] | None
    table_empty: bool | None
    overwrite: bool
    db_write_result: Any | None


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
        self.graph.add_node("upsert_only", self.upsert_only_node)
        self.graph.add_node("delete_and_upsert", self.delete_and_upsert_node)

        self.graph.add_node("decide_overwrite", self.decide_overwrite_node)

        self.graph.add_edge(START, "init_table")
        self.graph.add_edge("init_table", "check_empty")

        self.graph.add_conditional_edges(
            "check_empty",
            self.route_empty,
            {"empty": "run_pipeline", "not_empty": "decide_overwrite"},
        )

        self.graph.add_conditional_edges(
            "decide_overwrite",
            self.route_overwrite,
            {"true": "run_pipeline", "false": END},
        )

        self.graph.add_conditional_edges(
            "run_pipeline",
            self.route_after_pipeline,
            {"upsert_only": "upsert_only", "delete_and_upsert": "delete_and_upsert"},
        )

        self.graph.add_edge("upsert_only", END)
        self.graph.add_edge("delete_and_upsert", END)

        self.compiled = self.graph.compile()

    # ---- Routing ----
    def route_empty(self, state: IngestionState) -> str:
        return "empty" if state.get("table_empty") else "not_empty"

    def route_overwrite(self, state: IngestionState) -> str:
        return "true" if state.get("overwrite") else "false"

    def route_after_pipeline(self, state: IngestionState) -> str:
        return "delete_and_upsert" if state.get("overwrite") else "upsert_only"

    # ---- Nodes ----

    async def init_table_node(self, state: IngestionState) -> IngestionState:
        await self.init_table_fn()
        return state

    async def check_empty_node(self, state: IngestionState) -> IngestionState:
        count = await self.count_fn()
        state["table_empty"] = count == 0
        return state

    async def run_pipeline_node(self, state: IngestionState) -> IngestionState:
        result = await self.pipeline.run()
        state["pipeline_output"] = result.get("final_pipeline_output")
        return state

    async def upsert_only_node(self, state: IngestionState) -> IngestionState:
        records = state.get("pipeline_output") or []

        if not records:
            return state

        await self.upsert_fn(records=records)

        state["db_write_result"] = "upsert_only_done"
        return state

    async def delete_and_upsert_node(self, state: IngestionState) -> IngestionState:
        await self.delete_fn()

        records = state.get("pipeline_output") or []
        if not records:
            return state

        await self.upsert_fn(records=records)

        state["db_write_result"] = "delete_and_upsert_done"
        return state

    async def decide_overwrite_node(self, state: IngestionState) -> IngestionState:
        return state

    # ---- Runner ----
    async def run(self, overwrite: bool = True) -> IngestionState:
        initial_state: IngestionState = {
            "pipeline_output": None,
            "table_empty": None,
            "overwrite": overwrite,
            "db_write_result": None,
        }

        self.graph_saver.save(self.compiled)
        return await self.compiled.ainvoke(initial_state)  # type: ignore