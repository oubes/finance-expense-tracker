# ---- Imports ----
import logging
from typing import Any

from src.core.contracts.retrieval.retriever import RetrieverContract

logger = logging.getLogger(__name__)


# ---- Vector Retriever ----
class VectorRetriever(RetrieverContract):

    # ---- Constructor ----
    def __init__(self, db_client, embedding_fn, query_sql: str):
        self.db = db_client
        self.embedding_fn = embedding_fn
        self.query_sql = query_sql

    # ---- Search ----
    async def search(self, input_query: str, limit: int = 10) -> list[dict[str, Any]]:
        logger.info("stage=vector_retrieval_start")

        try:
            # ---- Input Validation ----
            if not input_query or not isinstance(input_query, str):
                raise ValueError("Invalid input_query provided")

            if limit <= 0:
                raise ValueError("Limit must be greater than 0")

            # ---- Embedding ----
            query_vector = await self._embed(input_query)

            if query_vector is None:
                raise RuntimeError("Embedding function returned None")

            # ---- Execution ----
            rows = await self._execute(query_vector, limit)

            logger.info("stage=vector_retrieval_completed")
            return rows or []

        except Exception as e:
            logger.exception("stage=vector_retrieval_failed")
            return []

    # ---- Embed ----
    async def _embed(self, input_query: str):
        try:
            return await self.embedding_fn.embed(input_query)
        except Exception:
            logger.exception("stage=embedding_failed")
            raise

    # ---- Execute ----
    async def _execute(self, query_vector, limit: int):
        try:
            params = (query_vector, query_vector, limit)
            return await self.db.execute(self.query_sql, params=params, fetch=True)
        except Exception:
            logger.exception("stage=db_execution_failed")
            raise