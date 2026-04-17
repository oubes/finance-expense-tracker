import logging
from source.infra_service.core.config.settings import AppSettings
from source.infra_service.adapters.vectordb_adapter import PostgresVectorClient

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
            # no pool init anymore
            self._initialized = True
            return True
        except Exception:
            logger.exception("Service start failed.")
            return False

    # ---- health check ----
    async def health(self) -> bool:
        try:
            result = await self.client.execute(
                "SELECT 1;",
                fetch=True
            )
            return result is not None

        except Exception:
            logger.exception("health check failed.")
            return False

    # ---- close system ----
    async def close(self):
        # no pool to close anymore
        self._initialized = False

    # ---- execute ----
    async def execute(self, query: str, params=None, fetch: bool = False):
        return await self.client.execute(query, params=params, fetch=fetch)

    # ---- execute one ----
    async def execute_one(self, query: str, params=None):
        return await self.client.execute_one(query, params=params)

    # ---- commit ----
    async def commit(self):
        return await self.client.commit()

    # ---- execute with keys ----
    async def execute_with_keys(self, query, keys, params=None, fetch=True):
        return await self.client.execute_with_keys(
            query=query,
            keys=keys,
            params=params,
            fetch=fetch
        )

    # ---- mapping ----
    def map_to_dicts(self, rows, keys):
        return self.client.map_to_dicts(rows, keys)