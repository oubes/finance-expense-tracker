# ---- Standard Library ----
import logging
from fastapi import Depends

# ---- Core ----
from src.core.config.settings import AppSettings
from src.bootstrap.dependencies.settings import get_settings
from src.bootstrap.dependencies.embeddings import get_embedding

# ---- DB Core ----
from src.infrastructure.vector_db.core.db_conn import DBConnect
from src.infrastructure.vector_db.core.db_exec import DBExecutor
from src.infrastructure.vector_db.extensions.db_vector_ext import VectorExtension
from src.infrastructure.vector_db.core.db_client import PostgresVectorClient
from src.modules.rag.retrieval.bm25_ret import BM25Retriever
from src.modules.rag.retrieval.vector_ret import VectorRetriever
from src.modules.rag.rerank.reranker import Reranker

# ---- Queries ----
from src.services.chunking.queries.chunk_queries import (
    CREATE_CHUNKS_TABLE_SQL,
    INSERT_CHUNK_SQL,
    DELETE_CHUNKS_SQL,
    COUNT_CHUNKS_SQL,
)

from src.services.retrieve.queries.rag_queries import BM25_QUERY, VECTOR_QUERY

# ---- Ops ----
from src.services.chunking.operations.chunk_ops import (
    init_chunks_table,
    upsert_chunks,
    delete_all_chunks,
    count_chunks,
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


# ---- BM25 Retriever ----
async def get_bm25_retriever(
    db_client: PostgresVectorClient = Depends(get_db_client),
) -> BM25Retriever:
    logger.info("Initializing BM25 Retriever")
    return BM25Retriever(
        db_client=db_client,
        query_sql=BM25_QUERY,
    )


# ---- Vector Retriever ----
async def get_vector_retriever(
    db_client: PostgresVectorClient = Depends(get_db_client),
    embedding_model=Depends(get_embedding),
) -> VectorRetriever:
    logger.info("Initializing Vector Retriever")
    return VectorRetriever(
        db_client=db_client,
        embedding_fn=embedding_model,
        query_sql=VECTOR_QUERY,
    )
    
    
async def get_reranker() -> Reranker:
    logger.info("Initializing Reranker")
    return Reranker()