import logging
from typing import Any

logger = logging.getLogger(__name__)

def _get(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)
    if hasattr(obj, key):
        return getattr(obj, key)
    raise KeyError(f"Missing key/attribute: {key}")

async def init_chunks_table(client, create_sql: str, config):
    try:
        sql = create_sql.format(dim=config.embeddings.dimension)
        await client.execute(sql)
        await client.commit()
        logger.info("Chunks table initialized.")
    except Exception:
        logger.exception("init_chunks_table failed")
        raise

async def upsert_chunks(client, insert_sql: str, records: list[Any]):
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
        logger.info(f"Upserted {len(records)} records")

    except Exception:
        logger.exception("upsert_chunks failed")
        raise

async def delete_all_chunks(client, delete_sql: str):
    try:
        await client.execute(delete_sql)
        await client.commit()
    except Exception:
        logger.exception("delete_all_chunks failed")
        raise

async def count_chunks(client, count_sql: str):
    try:
        result = await client.execute_one(count_sql)
        return result[0] if result else 0
    except Exception:
        logger.exception("count_chunks failed")
        return 0

async def preview_chunks(client, preview_sql: str, limit: int = 10):
    try:
        return await client.execute(preview_sql, (limit,), fetch=True)
    except Exception:
        logger.exception("preview_chunks failed")
        return []

async def search_chunks(client, search_sql: str, query_embedding, doc_name, limit):
    try:
        return await client.execute(
            search_sql,
            (query_embedding, doc_name, doc_name, query_embedding, limit),
            fetch=True,
        )
    except Exception:
        logger.exception("search_chunks failed")
        return []