# ---- Imports ----
import logging
from typing import Any

from src.infrastructure.vector_db.core.db_conn import DBConnect
from src.infrastructure.vector_db.extensions.db_vector_ext import VectorExtension
from src.infrastructure.vector_db.core.db_exec import DBExecutor

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)


# ---- Postgres Vector Client Class ----
class PostgresVectorClient:

    # ---- Constructor ----
    def __init__(
        self,
        conn: DBConnect,
        db_executor: DBExecutor,
        vector_ext: VectorExtension
    ):
        self.db = conn
        self.vector = vector_ext
        self.executor = db_executor

    # ---- Initialization ----
    async def init(self) -> bool:
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

    # ---- System Readiness Check ----
    async def is_system_ready(self) -> bool:
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

    # ---- Cleanup ----
    async def close(self) -> None:
        logger.info("Closing PostgresVectorClient...")

        try:
            await self.db.close()
            logger.info("Database connection closed successfully.")
        except Exception:
            logger.exception("Error while closing database connection.")

    # ---- Execute Query ----
    async def execute(
        self,
        query: str,
        params: tuple | None = None,
        fetch: bool = False
    ) -> list[dict[str, Any]] | None:
        return await self.executor.execute(query, params=params, fetch=fetch)  # type: ignore

    # ---- Execute Single Row Query ----
    async def execute_one(
        self,
        query: str,
        params: tuple | None = None
    ) -> dict[str, Any] | None:
        return await self.executor.execute_one(query, params=params)  # type: ignore

    # ---- Commit Transaction ----
    async def commit(self) -> None:
        await self.executor.commit()  # type: ignore

    # ---- Map Rows to Dicts ----
    def map_to_dicts(
        self,
        rows: list[tuple[Any, ...]] | list[dict[str, Any]],
        keys: list[str]
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []

        for row in rows:
            if isinstance(row, dict):
                result.append(row)
                continue

            if len(row) != len(keys):
                raise ValueError("Row length does not match keys length.")

            mapped: dict[str, Any] = {}
            for idx, key in enumerate(keys):
                mapped[key] = row[idx]

            result.append(mapped)

        return result

    # ---- Execute and Map to Dicts ----
    async def execute_with_keys(
        self,
        query: str,
        keys: list[str],
        params: tuple | None = None,
        fetch: bool = True
    ) -> list[dict[str, Any]] | None:
        rows = await self.execute(query, params=params, fetch=fetch)

        if rows is None:
            return None

        return self.map_to_dicts(rows, keys)