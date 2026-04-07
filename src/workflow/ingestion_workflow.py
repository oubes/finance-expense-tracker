# ---- Imports ----
from typing import TypedDict, Any
import logging

from langgraph.graph import StateGraph, START, END
from src.shared.graph_builder import GraphSaver
from src.core.schemas.pipeline.ingestion_schema import PipelineOutput

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ---- State Definition ----
class IngestionState(TypedDict):
    pipeline_output: PipelineOutput | None
    table_empty: bool | None
    overwrite: bool
    db_write_result: Any | None


# ---- Orchestrator ----
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

    # ---- Graph Builder ----
    def _build_graph(self) -> None:
        self.graph.add_node("init_table", self.init_table_node)
        self.graph.add_node("check_empty", self.check_empty_node)

        self.graph.add_node("run_pipeline", self.run_pipeline_node)
        self.graph.add_node("upsert_only", self.upsert_only_node)
        self.graph.add_node("delete_and_upsert", self.delete_and_upsert_node)

        self.graph.add_node("decide_overwrite", self.decide_overwrite_node)

        # ---- Entry Flow ----
        self.graph.add_edge(START, "init_table")
        self.graph.add_edge("init_table", "check_empty")

        self.graph.add_conditional_edges(
            "check_empty",
            self.route_empty,
            {
                "empty": "run_pipeline",
                "not_empty": "decide_overwrite",
            },
        )

        # ---- Overwrite Decision ----
        self.graph.add_conditional_edges(
            "decide_overwrite",
            self.route_overwrite,
            {
                "true": "run_pipeline",
                "false": END,
            },
        )

        # ---- Pipeline Output Routing (FIXED) ----
        self.graph.add_conditional_edges(
            "run_pipeline",
            self.route_after_pipeline,
            {
                "upsert_only": "upsert_only",
                "delete_and_upsert": "delete_and_upsert",
            },
        )

        # ---- Terminal Nodes ----
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
        try:
            logger.info("Init table started")
            await self.init_table_fn()
            logger.info("Init table success")
        except Exception:
            logger.exception("Init table failed")
            raise
        return state

    async def check_empty_node(self, state: IngestionState) -> IngestionState:
        try:
            logger.info("Checking if table is empty")
            count = await self.count_fn()
            state["table_empty"] = count == 0
            logger.info(f"Table empty: {state['table_empty']}")
        except Exception:
            logger.exception("Check empty failed")
            raise
        return state

    async def run_pipeline_node(self, state: IngestionState) -> IngestionState:
        try:
            logger.info("Running pipeline")
            result_state = await self.pipeline.run()
            output = result_state.get("final_pipeline_output")
            state["pipeline_output"] = output[0] if output else None
            logger.info("Pipeline completed successfully")
        except Exception:
            logger.exception("Pipeline execution failed")
            raise
        return state

    async def upsert_only_node(self, state: IngestionState) -> IngestionState:
        try:
            logger.info("Upsert only started")

            pipeline_output = state.get("pipeline_output")
            if not pipeline_output:
                logger.warning("No pipeline output, skipping upsert")
                return state

            data = pipeline_output.data
            doc_name = data[0].document.title if data else "default"

            chunks = []
            vectors = []

            for item in data:
                chunks.append({
                    "section": item.content.summary.title,
                    "content": item.content.text,
                    "metadata": item.dict() if hasattr(item, "dict") else str(item),
                })
                vectors.append(item.vector)

            await self.upsert_fn(
                doc_name=doc_name,
                chunks=chunks,
                vectors=vectors,
            )

            state["db_write_result"] = "upsert_only_done"
            logger.info("Upsert only completed successfully")

        except Exception:
            logger.exception("Upsert only failed")
            raise

        return state

    async def delete_and_upsert_node(self, state: IngestionState) -> IngestionState:
        try:
            logger.info("Delete and upsert started")

            await self.delete_fn()
            logger.info("Delete completed")

            pipeline_output = state.get("pipeline_output")
            if not pipeline_output:
                logger.warning("No pipeline output, skipping upsert")
                return state

            data = pipeline_output.data
            doc_name = data[0].document.title if data else "default"

            chunks = []
            vectors = []

            for item in data:
                chunks.append({
                    "section": item.content.summary.title,
                    "content": item.content.text,
                    "metadata": item.dict() if hasattr(item, "dict") else str(item),
                })
                vectors.append(item.vector)

            await self.upsert_fn(
                doc_name=doc_name,
                chunks=chunks,
                vectors=vectors,
            )

            state["db_write_result"] = "delete_and_upsert_done"
            logger.info("Delete and upsert completed successfully")

        except Exception:
            logger.exception("Delete and upsert failed")
            raise

        return state

    async def decide_overwrite_node(self, state: IngestionState) -> IngestionState:
        overwrite = state.get("overwrite", False)
        logger.info(f"Overwrite decision: {overwrite}")
        return state

    # ---- Runner ----
    async def run(self, overwrite: bool = False) -> IngestionState:
        initial_state: IngestionState = {
            "pipeline_output": None,
            "table_empty": None,
            "overwrite": overwrite,
            "db_write_result": None,
        }

        logger.info(f"Workflow started with overwrite={overwrite}")

        self.graph_saver.save(self.compiled)

        try:
            result = await self.compiled.ainvoke(initial_state)  # type: ignore
            logger.info("Workflow completed successfully")
            return result  # type: ignore
        except Exception:
            logger.exception("Workflow execution failed")
            raise