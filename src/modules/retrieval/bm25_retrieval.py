import logging
from typing import Any

logger = logging.getLogger(__name__)

# Executes BM25 search using external query
class BM25Retriever:
    def __init__(self, db_client, query_sql: str):
        self.db = db_client
        self.query_sql = query_sql

    # Run BM25 search
    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        logger.info("BM25 search started")
        params = (query, query, limit)
        rows = await self.db.execute(self.query_sql, params=params, fetch=True)
        logger.info(f"BM25 search returned {len(rows) if rows else 0} results")
        return rows or []