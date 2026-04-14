import logging
from typing import Any

from source.api_gateway.clients.base import BaseClient
from source.api_gateway.schemas.response.ingestion import IngestResponse
from source.api_gateway.schemas.response.health import ServiceHealthResponse

logger = logging.getLogger(__name__)


# ------------- Ingestion Service Client -------------
class IngestionClient(BaseClient):

    # ------------- Initialize -------------
    def __init__(self, base_url: str):
        logger.info("[INGESTION_CLIENT] initializing | base_url=%s", base_url)
        super().__init__(base_url)
        logger.info("[INGESTION_CLIENT] initialized successfully")

    # ------------- Ingestion Endpoint -------------
    async def ingest(self, payload: dict) -> IngestResponse:
        logger.info("[INGESTION_CLIENT] ingest request started")

        try:
            result = await self._request(
                "POST",
                "/ingest",
                json=payload,
            )

            return IngestResponse(
                status="success",
                data=result,
            )

        except Exception as e:
            logger.exception("[INGESTION_CLIENT] ingest FAILED")

            # IMPORTANT: propagate failure (don’t hide it)
            return IngestResponse(
                status="failed",
                data=None,
                error=str(e),
            )

    # ------------- Health Check -------------
    async def health(self) -> ServiceHealthResponse:
        logger.info("[INGESTION_CLIENT] health check started")

        try:
            await self._request("GET", "/health")

            return ServiceHealthResponse(
                status="up",
                service="ingestion",
                error=None,
            )

        except Exception as e:
            logger.warning(
                "[INGESTION_CLIENT] health UNREACHABLE",
                extra={"error": str(e)},
            )

            return ServiceHealthResponse(
                status="unreachable",
                service="ingestion",
                error=str(e),
            )