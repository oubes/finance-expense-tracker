# ---- Imports ----
import logging
from typing import Any

from source.api_gateway.adapters.base_adapter import BaseClient
from source.api_gateway.core.config.settings import Settings

logger = logging.getLogger(__name__)


# ------------- Ingestion Adapter -------------
class IngestionClient(BaseClient):

    def __init__(self, settings: Settings):
        self.base_url = settings.INGESTION_SERVICE_URL
        logger.info("[INGESTION_CLIENT] initializing | base_url=%s", self.base_url)
        super().__init__(base_url=self.base_url, settings=settings)
        logger.info("[INGESTION_CLIENT] initialized successfully")

    async def ingest(self, payload: dict) -> Any:
        logger.info("[INGESTION_CLIENT] ingest request started")

        response = await self._request(
            "POST",
            "/ingest",
            json=payload,
        )

        return response

    async def health(self) -> Any:
        logger.info("[INGESTION_CLIENT] health check started")

        return await self._request("GET", "/health")