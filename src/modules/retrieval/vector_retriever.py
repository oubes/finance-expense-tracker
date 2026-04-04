import logging
from typing import Any

logger = logging.getLogger(__name__)

# Executes vector similarity search
class VectorRetriever:
    def __init__(self, db_client, embedding_fn, query_sql: str):
        self.db = db_client
        self.embedding_fn = embedding_fn
        self.query_sql = query_sql

    # Run vector search pipeline
    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        logger.info("Vector search started")
        query_vector = await self._embed(query)
        rows = await self._execute(query_vector, limit)
        logger.info(f"Vector search returned {len(rows) if rows else 0} results")
        return rows or []

    # Generate embedding
    async def _embed(self, query: str):
        return await self.embedding_fn(query)

    # Execute vector query
    async def _execute(self, query_vector, limit: int):
        params = (query_vector, query_vector, limit)
        return await self.db.execute(self.query_sql, params=params, fetch=True)