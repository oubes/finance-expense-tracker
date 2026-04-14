from typing import Protocol
from source.api_gateway.schemas.response.ingestion import IngestResponse
from source.api_gateway.schemas.response.health import ServiceHealthResponse


class IngestionPort(Protocol):
    async def handle_message(self, message: str) -> IngestResponse:
        ...

    async def health(self) -> ServiceHealthResponse:
        ...