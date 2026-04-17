# ---- Imports ----
import logging
from typing import Any

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Helpers ----
def _get(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


# ---- Chunking Use Case ----
class ChunkingUseCase:

    def __init__(self, client):
        self.client = client

    # ---- INIT TABLE ----
    async def init_table(self, create_sql: str, config):
        logger.info("[ChunkingUseCase] init table start")

        try:
            sql = create_sql.format(dim=config.embeddings.dimension)

            await self.client.execute(sql)

            logger.info("[ChunkingUseCase] init table success")

        except Exception:
            logger.exception("[ChunkingUseCase] init table failed")
            raise

    # ---- UPSERT ----
    async def upsert(self, insert_sql: str, records: list[Any]):
        logger.info("[ChunkingUseCase] upsert start")

        try:
            for r in records:
                params = (
                    _get(r, "id"),
                    _get(r, "chunk_id"),
                    _get(r, "content"),
                    _get(r, "summary"),
                    _get(r, "embedding"),
                    _get(r, "chunk_title"),
                    _get(r, "doc_title"),
                    _get(r, "source"),
                    _get(r, "page"),
                    _get(r, "total_pages"),
                    _get(r, "created_at"),
                    _get(r, "pipeline_version"),
                    _get(r, "score"),
                )

                await self.client.execute(insert_sql, params)

            logger.info(f"[ChunkingUseCase] upsert completed | count={len(records)}")

        except Exception:
            logger.exception("[ChunkingUseCase] upsert failed")
            raise

    # ---- DELETE ALL ----
    async def delete_all(self, delete_sql: str):
        logger.info("[ChunkingUseCase] delete all start")

        try:
            await self.client.execute(delete_sql)

            logger.info("[ChunkingUseCase] delete all success")

        except Exception:
            logger.exception("[ChunkingUseCase] delete all failed")
            raise

    # ---- COUNT ----
    async def count(self, count_sql: str) -> int:
        logger.info("[ChunkingUseCase] count start")

        try:
            result = await self.client.execute_one(count_sql)

            if not result:
                return 0

            if isinstance(result, dict):
                count = list(result.values())[0]
            else:
                count = result[0]

            logger.info("[ChunkingUseCase] count completed")

            return count

        except Exception:
            logger.exception("[ChunkingUseCase] count failed")
            return 0