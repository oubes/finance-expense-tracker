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


def _to_params(r: Any) -> tuple:
    return (
        _get(r, "id"),
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


# ---- Chunking Use Case ----
class ChunkingUseCase:

    def __init__(self, client, queries, settings):
        self.db = client
        self.q = queries
        self.settings = settings

    # ---- INIT ----
    async def init(self) -> bool:
        logger.info("[Chunking Use Case] initializing...")

        try:
            table_exists = await self.db.execute_one(self.q.TABLE_EXISTS_SQL)
            print(table_exists)

            if table_exists and table_exists.get("to_regclass"):
                logger.info("[Chunking Use Case] chunks_table already initialized")
                return True

            sql = self.q.CREATE_CHUNKS_TABLE_SQL.format(
                dim=self.settings.embeddings.dimension
            )

            async with self.db:
                await self.db.execute(sql)

            logger.info("[Chunking Use Case] init success")
            return False

        except Exception as e:
            logger.exception("[Chunking Use Case] chunks_table init failed")
            raise RuntimeError("Failed to initialize chunks_table") from e

    # ---- HEALTH CHECK ----
    async def health(self):
        logger.info("[Chunking Use Case] health check start")

        try:
            table_exists = await self.db.execute_one(self.q.TABLE_EXISTS_SQL)

            if table_exists and table_exists.get("to_regclass"):
                logger.info("[Chunking Use Case] health check completed successfully")
                return True

            return False

        except Exception as e:
            logger.exception("[Chunking Use Case] health check failed")
            raise RuntimeError(
                "[Chunking Use Case] Chunks_table health check failed"
            ) from e

    # ---- UPSERT ----
    async def upsert(self, records: list[Any]) -> None:
        logger.info("[Chunking Use Case] upsert start")

        if not records:
            raise ValueError("records list is empty")

        try:
            params_list = [_to_params(r) for r in records]

            async with self.db:
                await self.db.executemany(
                    self.q.INSERT_CHUNK_SQL,
                    params_list
                )

            logger.info(
                f"[Chunking Use Case] upsert completed | count={len(records)}"
            )

        except Exception as e:
            logger.exception("[Chunking Use Case] upsert failed")
            raise RuntimeError(
                "[Chunking Use Case] Chunks_table upsert failed"
            ) from e

    # ---- DELETE ALL ----
    async def delete_all(self) -> None:
        logger.info("[Chunking Use Case] delete all start")

        try:
            async with self.db:
                await self.db.execute(self.q.DELETE_CHUNKS_SQL)

            logger.info("[Chunking Use Case] delete all success")

        except Exception as e:
            logger.exception("[Chunking Use Case] delete_all failed")
            raise RuntimeError(
                "[Chunking Use Case] Chunks_table delete_all failed"
            ) from e

    # ---- DROP TABLE ----
    async def drop_table(self) -> None:
        logger.info("[Chunking Use Case] drop table start")

        try:
            async with self.db:
                await self.db.execute(self.q.DROP_CHUNKS_TABLE_SQL)

            logger.info("[Chunking Use Case] drop table success")

        except Exception as e:
            logger.exception("[Chunking Use Case] drop_table failed")
            raise RuntimeError(
                "[Chunking Use Case] Chunks_table drop_table failed"
            ) from e

    # ---- COUNT ----
    async def count(self) -> int:
        logger.info("[Chunking Use Case] count start")

        try:
            row = await self.db.execute_one(self.q.COUNT_CHUNKS_SQL)

            if not row:
                return 0

            if isinstance(row, dict):
                return list(row.values())[0]

            return row[0]

        except Exception as e:
            logger.exception("[Chunking Use Case] count failed")
            raise RuntimeError("Chunk count failed") from e