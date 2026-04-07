# ---- Standard Library ----
import logging
from fastapi import Depends

# ---- Core ----
from src.core.config.settings import AppSettings
from src.bootstrap.dependencies.settings import get_settings

# ---- DB Core ----
from src.infrastructure.vector_db.core.db_conn import DBConnect
from src.infrastructure.vector_db.core.db_exec import DBExecutor
from src.infrastructure.vector_db.extensions.db_vector_ext import VectorExtension
from src.infrastructure.vector_db.core.db_client import PostgresVectorClient

# ---- Queries ----
from src.services.db_services.queries.chunk_queries import (
    CREATE_CHUNKS_TABLE_SQL,
    INSERT_CHUNK_SQL,
    DELETE_CHUNKS_SQL,
    COUNT_CHUNKS_SQL,
    PREVIEW_CHUNKS_SQL,
    SEARCH_CHUNKS_SQL
)

# ---- Ops ----
from src.services.db_services.operations.chunk_ops import (
    init_chunks_table,
    upsert_chunks,
    delete_all_chunks,
    count_chunks,
    preview_chunks,
    search_chunks
)

logger = logging.getLogger(__name__)


# ---- DB Connection ----
async def get_db_connection(settings: AppSettings = Depends(get_settings)):
    conn = DBConnect(settings=settings)
    await conn.connect()
    try:
        yield conn
    finally:
        await conn.close()


# ---- Executor ----
async def get_db_executor(conn=Depends(get_db_connection)):
    return DBExecutor(conn)


# ---- Vector Ext ----
async def get_vector_extension(conn=Depends(get_db_connection)):
    ext = VectorExtension(conn.conn)
    await ext.enable()
    return ext


# ---- Client ----
async def get_db_client(
    conn=Depends(get_db_connection),
    executor=Depends(get_db_executor),
    vector_ext=Depends(get_vector_extension),
):
    client = PostgresVectorClient(conn, executor, vector_ext)
    ok = await client.init()
    if not ok:
        raise RuntimeError("DB init failed")
    return client


# ---- Init ----
async def get_init_chunks_table(
    client=Depends(get_db_client),
    config: AppSettings = Depends(get_settings),
):
    async def _init():
        return await init_chunks_table(client, CREATE_CHUNKS_TABLE_SQL, config)
    return _init


# ---- Upsert ----
async def get_upsert_chunks(client=Depends(get_db_client)):
    async def _upsert(records: list[dict]):
        return await upsert_chunks(client, INSERT_CHUNK_SQL, records)
    return _upsert


# ---- Delete ----
async def get_delete_all_chunks(client=Depends(get_db_client)):
    async def _delete():
        return await delete_all_chunks(client, DELETE_CHUNKS_SQL)
    return _delete


# ---- Count ----
async def get_count_chunks(client=Depends(get_db_client)):
    async def _count():
        return await count_chunks(client, COUNT_CHUNKS_SQL)
    return _count


# ---- Preview ----
async def get_preview_chunks(client=Depends(get_db_client)):
    async def _preview(limit: int = 10):
        return await preview_chunks(client, PREVIEW_CHUNKS_SQL, limit)
    return _preview


# ---- Search ----
async def get_search_chunks(client=Depends(get_db_client)):
    async def _search(query_embedding, doc_name=None, limit=5):
        return await search_chunks(
            client,
            SEARCH_CHUNKS_SQL,
            query_embedding,
            doc_name,
            limit,
        )
    return _search