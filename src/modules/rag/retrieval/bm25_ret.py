# ---- Imports ----
import logging
from typing import Any

from src.core.contracts.retrieval.retriever import RetrieverContract

logger = logging.getLogger(__name__)


# ---- BM25 Retriever ----
class BM25Retriever(RetrieverContract):

    # ---- Constructor ----
    def __init__(self, db_client, query_sql: str):
        self.db = db_client
        self.query_sql = query_sql
    # ---- Search ----
    async def search(self, input_query: str, limit: int = 10) -> list[dict[str, Any]]:
        logger.info("stage=bm25_retrieval_start")

        try:
            # ---- Input Validation ----
            if not input_query or not isinstance(input_query, str):
                raise ValueError("Invalid input_query provided")

            if limit <= 0:
                raise ValueError("Limit must be greater than 0")

            # ---- Query Execution ----
            params = (input_query, input_query, limit)
            rows = await self.db.execute(self.query_sql, params=params, fetch=True)
            logger.info("stage=bm25_retrieval_completed")
            return rows or []

        except Exception:
            logger.exception("stage=bm25_retrieval_failed")
            return []