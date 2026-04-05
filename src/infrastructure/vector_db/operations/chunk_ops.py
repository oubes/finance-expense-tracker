# ---- Imports ----
import logging

from infrastructure.vector_db.queries.chunk_queries import (
    INSERT_CHUNK_SQL,
    DELETE_CHUNKS_SQL,
    COUNT_CHUNKS_SQL,
    PREVIEW_CHUNKS_SQL,
    SEARCH_CHUNKS_SQL,
    CREATE_CHUNKS_TABLE_SQL,
)

logger = logging.getLogger(__name__)


# ---- Initialize Chunks Table ----
# Creates the chunks table with the provided embedding dimension.
async def init_chunks_table(client, dim: int):
    try:
        create_sql = CREATE_CHUNKS_TABLE_SQL.format(dim=dim)
        await client.execute(create_sql)
        await client.commit()
        logger.info("Chunks table initialized successfully.")
    except Exception:
        logger.exception("init_chunks_table failed.")
        raise


# ---- Upsert Chunks ----
# Inserts chunks and their corresponding embeddings into the database.
async def upsert_chunks(client, doc_name, chunks, vectors):
    try:
        for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
            await client.execute(
                INSERT_CHUNK_SQL,
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
# Removes all stored chunks from the database.
async def delete_all_chunks(client):
    try:
        await client.execute(DELETE_CHUNKS_SQL)
        await client.commit()
        logger.info("All chunks deleted successfully.")
    except Exception:
        logger.exception("delete_all_chunks failed.")
        raise


# ---- Count Chunks ----
# Returns the total number of chunks stored in the database.
async def count_chunks(client):
    try:
        result = await client.execute_one(COUNT_CHUNKS_SQL)
        return result[0] if result else 0
    except Exception:
        logger.exception("count_chunks failed.")
        return 0


# ---- Preview Chunks ----
# Retrieves a limited preview of stored chunks.
async def preview_chunks(client, limit=10):
    try:
        rows = await client.execute(
            PREVIEW_CHUNKS_SQL,
            (limit,),
            fetch=True,
        )
        return rows or []
    except Exception:
        logger.exception("preview_chunks failed.")
        return []


# ---- Search Chunks ----
# Performs similarity search using query embedding and document filter.
async def search_chunks(client, query_embedding, doc_name, limit=5):
    try:
        rows = await client.execute(
            SEARCH_CHUNKS_SQL,
            (
                query_embedding,
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