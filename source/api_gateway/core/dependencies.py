# ---------- dependencies ----------

import logging
from functools import lru_cache
from fastapi import Depends

from source.api_gateway.core.settings import Settings
from source.api_gateway.clients.chat import ChatClient
from source.api_gateway.clients.ingestion import IngestionClient

logger = logging.getLogger(__name__)


@lru_cache
def get_settings() -> Settings:
    return Settings()


async def get_chat_client(settings: Settings = Depends(get_settings)) -> ChatClient:
    client = ChatClient(settings.CHAT_SERVICE_URL)
    await client.start()
    return client


async def get_ingestion_client(settings: Settings = Depends(get_settings)) -> IngestionClient:
    client = IngestionClient(settings.INGESTION_SERVICE_URL)
    await client.start()
    return client