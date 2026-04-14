from typing import Protocol, Any
from source.api_gateway.schemas.response.chat import ChatResponse
from source.api_gateway.schemas.response.health import ServiceHealthResponse


class ChatPort(Protocol):
    async def chat(self, message: str) -> ChatResponse:
        ...

    async def health(self) -> ServiceHealthResponse:
        ...