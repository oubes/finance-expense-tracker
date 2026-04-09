# ---- Imports ----
import logging
from typing import Any

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Helpers ----
def _get(obj: Any, key: str) -> Any:
    try:
        if isinstance(obj, dict):
            return obj.get(key)
        if hasattr(obj, key):
            return getattr(obj, key)
        raise KeyError(f"Missing key/attribute: {key}")
    except Exception:
        logger.exception("[helper] _get failed")
        raise


# ---- Init Table ----
async def init_chunks_table(client, create_sql: str, config):
    logger.info("[chunks_ops] init table start")

    try:
        sql = create_sql.format(dim=config.embeddings.dimension)

        await client.execute(sql)
        await client.commit()

        logger.info("[chunks_ops] init table success")

    except Exception:
        logger.exception("[chunks_ops] init table failed")
        raise


# ---- Upsert ----
async def upsert_chunks(client, insert_sql: str, records: list[Any]):
    logger.info("[chunks_ops] upsert start")

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
            await client.execute(insert_sql, params)

        await client.commit()

        logger.info(f"[chunks_ops] upsert completed | count={len(records)}")

    except Exception:
        logger.exception("[chunks_ops] upsert failed")
        raise


# ---- Delete All ----
async def delete_all_chunks(client, delete_sql: str):
    logger.info("[chunks_ops] delete all start")

    try:
        await client.execute(delete_sql)
        await client.commit()

        logger.info("[chunks_ops] delete all success")

    except Exception:
        logger.exception("[chunks_ops] delete all failed")
        raise


# ---- Count ----
async def count_chunks(client, count_sql: str):
    logger.info("[chunks_ops] count start")

    try:
        result = await client.execute_one(count_sql)
        count = result[0] if result else 0

        logger.info("[chunks_ops] count completed")

        return count

    except Exception:
        logger.exception("[chunks_ops] count failed")
        return 0