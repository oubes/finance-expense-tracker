# ---- Imports ----
import logging
from source.infra_service.core.config.settings import AppSettings
from source.infra_service.adapters.vectordb_adapter import PostgresVectorClient


# ---- Logger ----
logger = logging.getLogger(__name__)


class VectorDBService:

    def __init__(self, settings: AppSettings, client: PostgresVectorClient):
        self.settings = settings
        self.client = client
        self._initialized = False

    # ---- start system ----
    async def start(self) -> bool:
        logger.info("Starting VectorDBService...")

        try:
            # ---- critical: init client (pgvector setup) ----
            await self.client.init()

            self._initialized = True

            logger.info("VectorDBService started successfully")
            return True

        except Exception:
            logger.exception("Service start failed.")
            return False

    # ---- health check ----
    async def health(self, query: str) -> bool:
        try:
            result = await self.client.execute(
                query,
                fetch=True
            )

            return bool(result and result[0])

        except Exception:
            logger.exception("health check failed.")
            return False

    # ---- close system ----
    async def close(self):
        logger.info("Closing VectorDBService...")

        self._initialized = False

    # ---- guard helper (optional but useful) ----
    def _ensure_started(self):
        if not self._initialized:
            raise RuntimeError("VectorDBService not started")

    # ---- execute ----
    async def execute(self, query: str, params=None, fetch: bool = False):
        self._ensure_started()

        return await self.client.execute(
            query,
            params=params,
            fetch=fetch
        )

    # ---- execute one ----
    async def execute_one(self, query: str, params=None):
        self._ensure_started()

        return await self.client.execute_one(
            query,
            params=params
        )

    # ---- commit ----
    async def commit(self):
        self._ensure_started()

        return await self.client.commit()

    # ---- execute with keys ----
    async def execute_with_keys(self, query, keys, params=None, fetch=True):
        self._ensure_started()

        return await self.client.execute_with_keys(
            query=query,
            keys=keys,
            params=params,
            fetch=fetch
        )

    # ---- mapping ----
    def map_to_dicts(self, rows, keys):
        return self.client.map_to_dicts(rows, keys)