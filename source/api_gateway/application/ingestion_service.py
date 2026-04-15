import time
import logging

from source.api_gateway.adapters.ingestion_adapter import IngestionClient
from source.api_gateway.schemas.response.ingestion import IngestResponse
from source.api_gateway.schemas.response.health import ServiceHealthResponse
from source.api_gateway.core.observability.context import get_request_id, get_trace_id

logger = logging.getLogger(__name__)


class IngestionService:

    def __init__(self, ingestion_client: IngestionClient):
        self.ingestion_client = ingestion_client

    async def handle_message(self, message: str) -> IngestResponse:
        logger.info("[INGESTION_SERVICE] handle_message started")

        start = time.perf_counter()

        try:
            response = await self.ingestion_client.ingest(
                {"message": message}
            )

            latency_ms = (time.perf_counter() - start) * 1000

            return IngestResponse(
                status="up",
                data=response.json(),
                error=None,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000

            logger.exception("[INGESTION_SERVICE] handle_message failed")

            return IngestResponse(
                status="unreachable",
                data=None,
                error=str(e),
                latency_ms=latency_ms,
            )

    async def health(self) -> ServiceHealthResponse:
        logger.info(
            "[INGESTION_SERVICE] health check started",
            extra={
                "request_id": get_request_id(),
                "trace_id": get_trace_id(),
            },
        )

        try:
            response = await self.ingestion_client.health()

            return ServiceHealthResponse(
                status="up",
                service="ingestion",
                error=None if response.status_code == 200 else f"http_{response.status_code}",
            )

        except Exception as e:
            logger.warning(
                "[INGESTION_SERVICE] health UNREACHABLE",
                extra={
                    "error": str(e),
                    "request_id": get_request_id(),
                    "trace_id": get_trace_id(),
                },
            )

            return ServiceHealthResponse(
                status="unreachable",
                service="ingestion",
                error=str(e),
            )