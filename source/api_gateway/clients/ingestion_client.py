import logging
from source.api_gateway.clients.base_client import BaseClient
from source.api_gateway.schemas.ingestion import IngestResponse
from source.api_gateway.schemas.health import ServiceHealthResponse

# ---- Logger ----
logger = logging.getLogger(__name__)


# ------------- Ingestion Service Client -------------
class IngestionClient(BaseClient):

    # ------------- Initialize with Longer Timeout -------------
    def __init__(self, base_url: str):
        logger.info("[INGESTION_CLIENT] initializing | base_url=%s", base_url)
        super().__init__(base_url, timeout=30.0)
        logger.info("[INGESTION_CLIENT] initialized successfully")

    # ------------- Ingestion Endpoint -------------
    async def ingest(self, payload: dict) -> IngestResponse:

        logger.info("[INGESTION_CLIENT] ingest request started")

        try:
            result = await self._request(
                "POST",
                f"{self.base_url}/ingest",
                json=payload
            )

            return IngestResponse(
                status="success",
                data=result
            )

        except Exception as e:
            logger.warning(
                "[INGESTION_CLIENT] ingest FAILED | error=%s",
                str(e)
            )

            return IngestResponse(
                status="failed",
                error=str(e)
            )

    # ------------- Health Check -------------
    async def health(self) -> ServiceHealthResponse:
        logger.info("[INGESTION_CLIENT] health check started")

        try:
            result = await self._request(
                "GET",
                f"{self.base_url}/health"
            )

            return ServiceHealthResponse(
                status="up",
                service="ingestion",
                error=None
            )

        except Exception as e:
            logger.warning(
                "[INGESTION_CLIENT] health UNREACHABLE | error=%s",
                repr(e)
            )

            return ServiceHealthResponse(
                status="unreachable",
                service="ingestion",
                error=str(e)
            )