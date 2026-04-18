# ---- Imports ----
import logging
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector_async

from source.infra_service.core.config.settings import AppSettings


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Postgres Vector Client ----
class PostgresVectorClient:

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self._initialized = False

        self._conn: AsyncConnection | None = None

    # ---- connection ----
    async def connect(self):
        if self._conn is None:
            self._conn = await AsyncConnection.connect(
                self.settings.postgres_full_url
            )

    # ---- init (run once) ----
    async def init(self):
        if self._initialized:
            return

        try:
            conn = await AsyncConnection.connect(
                self.settings.postgres_full_url
            )

            await register_vector_async(conn)
            await conn.close()

            self._initialized = True

            logger.info("pgvector registered successfully")

        except Exception as e:
            logger.exception("pgvector init failed")
            raise RuntimeError("Failed to initialize pgvector") from e

    # ---- execute ----
    async def execute(self, query: str, params=None, fetch: bool = False):
        await self.connect()

        try:
            async with self._conn.cursor(row_factory=dict_row) as cur:  # type: ignore
                await cur.execute(query, params or ()) # type: ignore

                if fetch:
                    return await cur.fetchall()

                return None

        except Exception as e:
            logger.exception("execute failed")
            raise RuntimeError("Postgres execute failed") from e

    # ---- execute one ----
    async def execute_one(self, query: str, params=None):
        await self.connect()

        try:
            async with self._conn.cursor(row_factory=dict_row) as cur:  # type: ignore
                await cur.execute(query, params or ()) # type: ignore
                return await cur.fetchone()

        except Exception as e:
            logger.exception("execute_one failed")
            raise RuntimeError("Postgres execute_one failed") from e

    # ---- commit ----
    async def commit(self):
        if not self._conn:
            return

        try:
            await self._conn.commit()

        except Exception as e:
            logger.exception("commit failed")
            raise RuntimeError("Postgres commit failed") from e

    # ---- rollback ----
    async def rollback(self):
        if not self._conn:
            return

        try:
            await self._conn.rollback()

        except Exception as e:
            logger.exception("rollback failed")
            raise RuntimeError("Postgres rollback failed") from e

    # ---- close ----
    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None

    # ---- context manager ----
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc:
                await self.rollback()
            else:
                await self.commit()
        finally:
            await self.close()

    # ---- mapping ----
    def map_to_dicts(self, rows, keys):
        return [
            row if isinstance(row, dict)
            else {k: row[i] for i, k in enumerate(keys)}
            for row in rows
        ]

    # ---- execute + map ----
    async def execute_with_keys(self, query, keys, params=None, fetch=True):
        rows = await self.execute(query, params=params, fetch=fetch)

        if not rows:
            return []

        return self.map_to_dicts(rows, keys)