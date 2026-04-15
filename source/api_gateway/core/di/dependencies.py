from fastapi import Depends, Request
from functools import lru_cache

from source.api_gateway.core.config.settings import Settings
from source.api_gateway.adapters import ChatClient, IngestionClient
from source.api_gateway.application import ChatService, IngestionService
from source.api_gateway.core.observability.context import (
    get_request_id,
    get_trace_id,
    set_request_context,
)


@lru_cache
def get_settings() -> Settings:
    return Settings()


async def get_chat_client(request: Request) -> ChatClient:
    return request.app.state.chat_client


async def get_ingestion_client(request: Request) -> IngestionClient:
    return request.app.state.ingestion_client


async def get_chat_service(
    chat_client: ChatClient = Depends(get_chat_client),
) -> ChatService:
    return ChatService(chat_client)


async def get_ingestion_service(
    request: Request,
    ingestion_client: IngestionClient = Depends(get_ingestion_client),
) -> IngestionService:

    request_id = getattr(request.state, "request_id", None) or get_request_id() or ""
    trace_id = getattr(request.state, "trace_id", None) or get_trace_id() or ""

    set_request_context(
        request_id=request_id,
        trace_id=trace_id,
        service_name="api_gateway",
    )

    return IngestionService(ingestion_client)