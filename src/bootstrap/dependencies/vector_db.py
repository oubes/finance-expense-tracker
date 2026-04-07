# ---- Standard Library ----
import logging
from fastapi import Depends

# ---- Core Config ----
from src.core.config.settings import AppSettings
from src.bootstrap.dependencies.settings import get_settings

# ---- Infrastructure ----
from src.infrastructure.vector_db.core.db_conn import DBConnect
from src.infrastructure.vector_db.core.db_exec import DBExecutor
from src.infrastructure.vector_db.extensions.db_vector_ext import VectorExtension
from src.infrastructure.vector_db.core.db_client import PostgresVectorClient

from src.infrastructure.vector_db.queries.chunk_queries import (
    CREATE_CHUNKS_TABLE_SQL,
    INSERT_CHUNK_SQL,
    DELETE_CHUNKS_SQL,
    COUNT_CHUNKS_SQL,
    PREVIEW_CHUNKS_SQL,
    SEARCH_CHUNKS_SQL
)

from src.infrastructure.vector_db.operations.chunk_ops import (
    init_chunks_table,
    upsert_chunks,
    delete_all_chunks,
    count_chunks,
    preview_chunks,
    search_chunks
)

logger = logging.getLogger(__name__)


# ---- DB Connection (Single Source of Truth) ----
async def get_db_connection(
    settings: AppSettings = Depends(get_settings),
) -> DBConnect:
    logger.info("Creating DB connection")

    conn = DBConnect(settings=settings)

    await conn.connect()

    try:
        yield conn
    finally:
        await conn.close()


# ---- DB Executor ----
async def get_db_executor(
    conn: DBConnect = Depends(get_db_connection),
) -> DBExecutor:
    logger.info("Creating DB executor")
    return DBExecutor(conn)


# ---- Vector Extension ----
async def get_vector_extension(
    conn: DBConnect = Depends(get_db_connection),
) -> VectorExtension:
    logger.info("Creating Vector Extension")

    vector_ext = VectorExtension(conn.conn)
    await vector_ext.enable()

    return vector_ext


# ---- Postgres Vector Client ----
async def get_db_client(
    conn: DBConnect = Depends(get_db_connection),
    executor: DBExecutor = Depends(get_db_executor),
    vector_ext: VectorExtension = Depends(get_vector_extension),
):
    logger.info("Creating PostgresVectorClient")

    client = PostgresVectorClient(
        conn=conn,
        db_executor=executor,
        vector_ext=vector_ext,
    )

    ok = await client.init()
    if not ok:
        raise RuntimeError("Failed to initialize PostgresVectorClient")

    return client


# ---- Chunk Operations Wrappers ----

# ---- Initialize Table ----
async def get_init_chunks_table(
    client: PostgresVectorClient = Depends(get_db_client),
    config: AppSettings = Depends(get_settings),
):
    async def _init() -> None:
        return await init_chunks_table(
            client=client,
            create_sql=CREATE_CHUNKS_TABLE_SQL,
            config=config,
        )

    return _init


# ---- Upsert Chunks ----
async def get_upsert_chunks(
    client: PostgresVectorClient = Depends(get_db_client),
):
    async def _upsert(
        doc_name: str,
        chunks: list[dict],
        vectors: list[list[float]],
    ) -> None:
        return await upsert_chunks(
            client=client,
            insert_sql=INSERT_CHUNK_SQL,
            doc_name=doc_name,
            chunks=chunks,
            vectors=vectors,
        )

    return _upsert


# ---- Delete All Chunks ----
async def get_delete_all_chunks(
    client: PostgresVectorClient = Depends(get_db_client),
):
    async def _delete() -> None:
        return await delete_all_chunks(
            client=client,
            delete_sql=DELETE_CHUNKS_SQL,
        )

    return _delete


# ---- Count Chunks ----
async def get_count_chunks(
    client: PostgresVectorClient = Depends(get_db_client),
):
    async def _count() -> int:
        return await count_chunks(
            client=client,
            count_sql=COUNT_CHUNKS_SQL,
        )

    return _count


# ---- Preview Chunks ----
async def get_preview_chunks(
    client: PostgresVectorClient = Depends(get_db_client),
):
    async def _preview(limit: int = 10):
        return await preview_chunks(
            client=client,
            preview_sql=PREVIEW_CHUNKS_SQL,
            limit=limit,
        )

    return _preview


# ---- Search Chunks ----
async def get_search_chunks(
    client: PostgresVectorClient = Depends(get_db_client),
):
    async def _search(
        query_embedding: list[float],
        doc_name: str | None = None,
        limit: int = 5,
    ):
        return await search_chunks(
            client=client,
            search_sql=SEARCH_CHUNKS_SQL,
            query_embedding=query_embedding,
            doc_name=doc_name,
            limit=limit,
        )

    return _search