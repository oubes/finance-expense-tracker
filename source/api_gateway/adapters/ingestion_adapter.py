from typing import Any

from source.api_gateway.adapters.base_adapter import BaseClient
from source.api_gateway.core.config.settings import Settings


class IngestionClient(BaseClient):

    def __init__(self, settings: Settings):
        super().__init__(
            base_url=settings.INGESTION_SERVICE_URL,
            settings=settings,
        )

    async def ingest(self, payload: dict) -> Any:
        return await self._request(
            "POST",
            "/ingest",
            json=payload,
        )

    async def health(self) -> Any:
        return await self._request("GET", "/health")