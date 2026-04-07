# ---- Imports ----
import logging

logger = logging.getLogger(__name__)
from src.core.config.settings import AppSettings


# ---- Initialize Chunks Table ----
# Creates the chunks table with injected SQL.
async def init_chunks_table(client, create_sql: str, config: AppSettings):
    try:
        sql = create_sql.format(dim=config.embeddings.dimension)
        await client.execute(sql)
        await client.commit()
        logger.info("Chunks table initialized successfully.")
    except Exception:
        logger.exception("init_chunks_table failed.")
        raise


# ---- Upsert Chunks ----
# Inserts chunks using injected SQL.
async def upsert_chunks(client, insert_sql: str, doc_name: str, chunks, vectors):
    try:
        for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
            await client.execute(
                insert_sql,
                (
                    doc_name,
                    chunk["section"],
                    i,
                    chunk["content"],
                    vec,
                ),
            )

        await client.commit()
        logger.info(f"Upserted {len(chunks)} chunks for doc: {doc_name}")

    except Exception:
        logger.exception("upsert_chunks failed.")
        raise


# ---- Delete All Chunks ----
async def delete_all_chunks(client, delete_sql: str):
    try:
        await client.execute(delete_sql)
        await client.commit()
        logger.info("All chunks deleted successfully.")
    except Exception:
        logger.exception("delete_all_chunks failed.")
        raise


# ---- Count Chunks ----
async def count_chunks(client, count_sql: str):
    try:
        result = await client.execute_one(count_sql)
        return result[0] if result else 0
    except Exception:
        logger.exception("count_chunks failed.")
        return 0


# ---- Preview Chunks ----
async def preview_chunks(client, preview_sql: str, limit: int = 10):
    try:
        rows = await client.execute(
            preview_sql,
            (limit,),
            fetch=True,
        )
        return rows or []
    except Exception:
        logger.exception("preview_chunks failed.")
        return []


# ---- Search Chunks ----
async def search_chunks(
    client,
    search_sql: str,
    query_embedding,
    doc_name: str | None,
    limit: int = 5,
):
    try:
        rows = await client.execute(
            search_sql,
            (
                query_embedding,
                doc_name,
                doc_name,
                query_embedding,
                limit,
            ),
            fetch=True,
        )
        return rows or []
    except Exception:
        logger.exception("search_chunks failed.")
        return []