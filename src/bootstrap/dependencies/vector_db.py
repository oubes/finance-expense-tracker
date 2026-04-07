# ---- Standard Library ----
import logging

# ---- FastAPI ----
from fastapi import Depends

# ---- Core Config ----
from src.core.config.settings import AppSettings
from src.bootstrap.dependencies.settings import get_settings

# ---- Infrastructure ----
from src.infrastructure.vector_db.core.db_conn import DBConnect
from src.infrastructure.vector_db.core.db_exec import DBExecutor
from src.infrastructure.vector_db.extensions.db_vector_ext import VectorExtension
from src.infrastructure.vector_db.core.db_client import PostgresVectorClient

logger = logging.getLogger(__name__)


# ---- DB Connection ----
async def get_db_connection(settings: AppSettings = Depends(get_settings)) -> DBConnect:
    logger.info("Creating DB connection")
    conn = DBConnect(settings=settings)

    if hasattr(conn, "connect") and callable(conn.connect):
        result = conn.connect()
        if hasattr(result, "__await__"):
            await result
        else:
            await conn.connect()

    return conn


# ---- DB Executor ----
async def get_db_executor(conn: DBConnect = Depends(get_db_connection)) -> DBExecutor:
    logger.info("Creating DB executor")
    return DBExecutor(conn)


# ---- Vector Extension ----
async def get_vector_extension(conn: DBConnect = Depends(get_db_connection)) -> VectorExtension:
    logger.info("Creating Vector Extension")
    vector_ext = VectorExtension(conn.conn)
    await vector_ext.enable()
    return vector_ext


# ---- Postgres Vector Client ----
async def get_db_client(
    conn: DBConnect = Depends(get_db_connection),
    executor: DBExecutor = Depends(get_db_executor),
    vector_ext: VectorExtension = Depends(get_vector_extension),
) -> PostgresVectorClient:
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