# ---- Imports ----
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from source.api_gateway.adapters.chat_adapter import ChatClient
from source.api_gateway.adapters.ingestion_adapter import IngestionClient

from source.api_gateway.core.config.settings import Settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("[LIFESPAN] startup initiated")

    # ---- Startup ----
    settings = Settings()

    chat_client = ChatClient(settings=settings)
    await chat_client.start()

    ingestion_client = IngestionClient(settings=settings)
    await ingestion_client.start()

    app.state.chat_client = chat_client
    app.state.ingestion_client = ingestion_client

    logger.info("[LIFESPAN] clients initialized")

    try:
        yield
    finally:
        # ---- Shutdown ----
        logger.info("[LIFESPAN] shutdown initiated")

        await chat_client.close()
        await ingestion_client.close()

        logger.info("[LIFESPAN] shutdown completed")