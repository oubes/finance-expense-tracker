# ---------- dependencies ----------
import logging
from functools import lru_cache
from fastapi import Depends, Request

from source.api_gateway.core.config.settings import Settings
from source.api_gateway.adapters import ChatClient, IngestionClient
from source.api_gateway.application import ChatService, IngestionService

# ---- Logger ----
logger = logging.getLogger(__name__)


@lru_cache
def get_settings() -> Settings:
    return Settings()


# ---- Clients ----
async def get_chat_client(request: Request) -> ChatClient:
    client = request.app.state.chat_client
    return client


async def get_ingestion_client(request: Request) -> IngestionClient:
    client = request.app.state.ingestion_client
    return client

# ---- Services ----
async def get_chat_service(
    chat_client: ChatClient = Depends(get_chat_client),
) -> ChatService:
    return ChatService(chat_client)


async def get_ingestion_service(
    ingestion_client: IngestionClient = Depends(get_ingestion_client),
) -> IngestionService:
    return IngestionService(ingestion_client)