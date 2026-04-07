# ---- Imports ----
from typing import TypedDict, Any
import logging
import asyncio

from langgraph.graph import StateGraph, START, END
from src.shared.graph_builder import GraphSaver
from src.bootstrap.dependencies.vector_db import (
    get_db_client,
    get_init_chunks_table,
    get_upsert_chunks,
    get_delete_all_chunks,
    get_count_chunks,
)

from src.core.schemas.pipeline.ingestion_schema import PipelineOutput

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ---- State Definition ----
class IngestionState(TypedDict):
    pipeline_output: PipelineOutput | None
    table_exists: bool | None
    table_empty: bool | None
    db_action: str | None
    db_write_result: Any | None


# ---- Orchestrator ----
class IngestionWorkflow:

    def __init__(self, pipeline) -> None:
        self.pipeline = pipeline
        self.graph = StateGraph(IngestionState)
        self._build_graph()
        self.graph_saver = GraphSaver("ingestion_workflow.png")

    # ---- Graph Builder ----
    def _build_graph(self) -> None:
        self.graph.add_node("check_table", self.check_table_node)
        self.graph.add_node("init_table", self.init_table_node)
        self.graph.add_node("check_empty", self.check_empty_node)

        self.graph.add_node("run_pipeline", self.run_pipeline_node)

        self.graph.add_node("decide_action", self.decide_action_node)
        self.graph.add_node("delete_and_upsert", self.delete_and_upsert_node)
        self.graph.add_node("upsert_only", self.upsert_only_node)
        self.graph.add_node("skip", self.skip_node)

        self.graph.add_edge(START, "check_table")

        # ---- Table routing ----
        self.graph.add_conditional_edges(
            "check_table",
            self.route_table_exists,
            {
                "init": "init_table",
                "exists": "check_empty",
            },
        )

        # ---- Both paths converge into pipeline (ONLY when needed) ----
        self.graph.add_edge("init_table", "run_pipeline")

        self.graph.add_conditional_edges(
            "check_empty",
            self.route_empty_table,
            {
                "empty": "run_pipeline",
                "not_empty": "decide_action",
            },
        )

        # ---- After pipeline ----
        self.graph.add_edge("run_pipeline", "upsert_only")

        # ---- Decision for non-empty table ----
        self.graph.add_conditional_edges(
            "decide_action",
            self.route_db_action,
            {
                "skip": "skip",
                "delete_and_upsert": "run_pipeline_existing",
            },
        )

        self.graph.add_node("run_pipeline_existing", self.run_pipeline_existing_node)

        self.graph.add_edge("run_pipeline_existing", "delete_and_upsert")

        # ---- Ends ----
        self.graph.add_edge("upsert_only", END)
        self.graph.add_edge("skip", END)
        self.graph.add_edge("delete_and_upsert", END)

        self.compiled = self.graph.compile()

    # ---- Routing ----
    def route_table_exists(self, state: IngestionState) -> str:
        return "exists" if state.get("table_exists") else "init"

    def route_empty_table(self, state: IngestionState) -> str:
        return "empty" if state.get("table_empty") else "not_empty"

    def route_db_action(self, state: IngestionState) -> str:
        return state.get("db_action") or "skip"

    # ---- Nodes ----

    def check_table_node(self, state: IngestionState) -> IngestionState:
        async def _check():
            client = await get_db_client()
            result = await client.execute_one(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'chunk_embeddings');"
            )
            return result[0] if result else False

        state["table_exists"] = asyncio.run(_check())
        return state

    def init_table_node(self, state: IngestionState) -> IngestionState:
        async def _init():
            init_fn = await get_init_chunks_table()
            await init_fn()

        asyncio.run(_init())
        state["table_exists"] = True
        state["table_empty"] = True
        return state

    def check_empty_node(self, state: IngestionState) -> IngestionState:
        async def _count():
            count_fn = await get_count_chunks()
            return await count_fn()

        count = asyncio.run(_count())
        state["table_empty"] = count == 0
        return state

    # ---- Pipeline (shared) ----
    def run_pipeline_node(self, state: IngestionState) -> IngestionState:
        result_state = self.pipeline.run()
        pipeline_output = result_state.get("final_pipeline_output")

        if not pipeline_output:
            state["pipeline_output"] = None
            return state

        state["pipeline_output"] = pipeline_output[0]
        return state

    def run_pipeline_existing_node(self, state: IngestionState) -> IngestionState:
        return self.run_pipeline_node(state)

    # ---- Decision ----
    def decide_action_node(self, state: IngestionState) -> IngestionState:
        if not state.get("pipeline_output"):
            state["db_action"] = "skip"
            return state

        state["db_action"] = "delete_and_upsert"
        return state

    # ---- DB Actions ----
    def delete_and_upsert_node(self, state: IngestionState) -> IngestionState:
        async def _run():
            delete_fn = await get_delete_all_chunks()
            upsert_fn = await get_upsert_chunks()

            await delete_fn()

            pipeline_output = state["pipeline_output"]
            if not pipeline_output:
                return

            data = pipeline_output.data
            doc_name = data[0].document.title if data else "default"

            chunks = []
            vectors = []

            for item in data:
                chunks.append({
                    "section": item.content.summary.title,
                    "content": item.content.text,
                })
                vectors.append(item.vector)

            await upsert_fn(doc_name=doc_name, chunks=chunks, vectors=vectors)

        asyncio.run(_run())
        state["db_write_result"] = "delete_and_upsert_done"
        return state

    def upsert_only_node(self, state: IngestionState) -> IngestionState:
        async def _run():
            upsert_fn = await get_upsert_chunks()

            pipeline_output = state["pipeline_output"]
            if not pipeline_output:
                return

            data = pipeline_output.data
            doc_name = data[0].document.title if data else "default"

            chunks = []
            vectors = []

            for item in data:
                chunks.append({
                    "section": item.content.summary.title,
                    "content": item.content.text,
                })
                vectors.append(item.vector)

            await upsert_fn(doc_name=doc_name, chunks=chunks, vectors=vectors)

        asyncio.run(_run())
        state["db_write_result"] = "upsert_only_done"
        return state

    def skip_node(self, state: IngestionState) -> IngestionState:
        state["db_write_result"] = "skipped"
        return state

    # ---- Runner ----
    def run(self) -> IngestionState:
        initial_state: IngestionState = {
            "pipeline_output": None,
            "table_exists": None,
            "table_empty": None,
            "db_action": None,
            "db_write_result": None,
        }

        self.graph_saver.save(self.compiled)
        return self.compiled.invoke(initial_state)  # type: ignore