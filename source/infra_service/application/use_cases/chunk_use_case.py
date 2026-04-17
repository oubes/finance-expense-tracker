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


# ---- Chunking Use Case ----
class ChunkingUseCase:

    def __init__(self, client, queries):
        self.db = client
        self.q = queries

    # ---- INIT ----
    async def init(self, config) -> bool:
        logger.info("[Chunking Use Case] initializing...")

        try:
            sql = self.q.CREATE_TABLE.format(dim=config.embeddings.dimension)

            await self.db.execute(sql)
            await self.db.commit()

            return True

        except Exception:
            logger.exception("[Chunking Use Case] init failed")
            return False

    # ---- UPSERT ----
    async def upsert(self, records: list[Any]) -> bool:
        logger.info("[Chunking Use Case] upsert start")

        try:
            if not records:
                raise ValueError("records list is empty")

            params_list = [_to_params(r) for r in records]

            await self.db.executemany(self.q.INSERT_CHUNK, params_list)
            await self.db.commit()

            logger.info(f"[Chunking Use Case] upsert completed | count={len(records)}")
            return True

        except Exception:
            logger.exception("[Chunking Use Case] upsert failed")
            return False

    # ---- DELETE ALL ----
    async def delete_all(self) -> bool:
        logger.info("[Chunking Use Case] delete all start")

        try:
            await self.db.execute(self.q.DELETE_ALL)
            await self.db.commit()

            logger.info("[Chunking Use Case] delete all success")
            return True

        except Exception:
            logger.exception("[Chunking Use Case] delete_all failed")
            return False

    # ---- COUNT ----
    async def count(self) -> int:
        logger.info("[Chunking Use Case] count start")

        try:
            row = await self.db.execute_one(self.q.COUNT_ALL)

            if not row:
                return 0

            if isinstance(row, dict):
                return list(row.values())[0]

            return row[0]

        except Exception:
            logger.exception("[Chunking Use Case] count failed")
            return 0