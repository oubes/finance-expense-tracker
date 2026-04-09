# ---- Imports ----
import logging

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Search ----
async def search_chunks(
    client,
    search_sql: str,
    query_embedding,
    doc_name,
    limit: int
):
    logger.info("[rag_ops] search start")

    try:
        result = await client.execute(
            search_sql,
            (query_embedding, doc_name, doc_name, query_embedding, limit),
            fetch=True,
        )

        logger.info("[rag_ops] search completed")

        return result

    except Exception:
        logger.exception("[rag_ops] search failed")
        return []


# ---- Preview ----
async def preview_chunks(client, preview_sql: str, limit: int = 10):
    logger.info("[rag_ops] preview start")

    try:
        result = await client.execute(preview_sql, (limit,), fetch=True)

        logger.info("[rag_ops] preview completed")

        return result

    except Exception:
        logger.exception("[rag_ops] preview failed")
        return []