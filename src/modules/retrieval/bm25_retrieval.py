# ---- Imports ----
import logging
from typing import Any

logger = logging.getLogger(__name__)


# ---- BM25 Retriever ----
# Executes BM25 search using an injected SQL query and database client.
class BM25Retriever:
    def __init__(self, db_client, query_sql: str):
        self.db = db_client
        self.query_sql = query_sql

    # ---- Search ----
    # Runs BM25 full-text search and returns ranked results.
    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        logger.info("BM25 search started")
        params = (query, query, limit)
        rows = await self.db.execute(self.query_sql, params=params, fetch=True)
        logger.info(f"BM25 search returned {len(rows) if rows else 0} results")
        return rows or []