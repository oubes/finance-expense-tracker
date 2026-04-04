import logging

from src.infrastructure.vector_db.core.db_conn import DBConnect
from src.infrastructure.vector_db.extensions.db_vector_ext import VectorExtension
from src.infrastructure.vector_db.core.db_exec import DBExecutor

logger = logging.getLogger(__name__)

class PostgresVectorClient:

    def __init__(self, conn: DBConnect):
        self.db = conn
        self.vector = None
        self.executor = None

    async def init(self):
        logger.info("Initializing PostgresVectorClient...")

        if not await self.db.connect():
            logger.error("Database connection failed.")
            return False

        logger.info("Database connected successfully.")

        self.executor = DBExecutor(self.db)

        self.vector = VectorExtension(self.db.conn)

        if not await self.vector.enable():
            logger.error("Failed to enable pgvector extension.")
            return False

        logger.info("pgvector extension enabled.")
        return True

    async def is_system_ready(self):
        logger.debug("Checking system readiness...")

        db_ok = await self.db.is_alive()
        vector_ok = self.vector.is_enabled() if self.vector else False

        if not db_ok:
            logger.warning("Database is not alive.")

        if not vector_ok:
            logger.warning("Vector extension is not enabled.")

        ready = db_ok and vector_ok
        logger.info(f"System readiness: {ready}")
        return ready

    async def close(self):
        logger.info("Closing PostgresVectorClient...")

        try:
            await self.db.close()
            logger.info("Database connection closed successfully.")
        except Exception:
            logger.exception("Error while closing database connection.")

    async def execute(self, query, params=None, fetch: bool = False):
        return await self.executor.execute(query, params=params, fetch=fetch) # type: ignore

    async def execute_one(self, query, params=None):
        return await self.executor.execute_one(query, params=params) # type: ignore

    async def commit(self):
        await self.executor.commit() # type: ignore