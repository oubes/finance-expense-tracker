# ---- Imports ----
import logging
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector_async

from source.infra_service.core.config.settings import AppSettings

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Postgres Vector Client (NO POOL) ----
class PostgresVectorClient:

    def __init__(self, settings: AppSettings):
        self.settings = settings

    # ---- internal connection ----
    async def _connect(self):
        return await AsyncConnection.connect(
            self.settings.postgres_full_url
        )

    # ---- execute ----
    async def execute(self, query: str, params=None, fetch: bool = False):
        conn = None

        try:
            conn = await self._connect()

            # register pgvector support
            await register_vector_async(conn)

            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params or ()) # type: ignore

                if fetch:
                    return await cur.fetchall()

                return None

        except Exception:
            logger.exception("execute failed.")
            return None

        finally:
            if conn:
                await conn.close()

    # ---- execute one ----
    async def execute_one(self, query: str, params=None):
        conn = None

        try:
            conn = await self._connect()

            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, params or ()) # type: ignore
                return await cur.fetchone()

        except Exception:
            logger.exception("execute_one failed.")
            return None

        finally:
            if conn:
                await conn.close()

    # ---- commit ----
    async def commit(self):
        conn = None

        try:
            conn = await self._connect()
            await conn.commit()

        except Exception:
            logger.exception("commit failed.")

        finally:
            if conn:
                await conn.close()

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
            return None

        return self.map_to_dicts(rows, keys)