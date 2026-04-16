# ---- Imports ----
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from source.ingestion_service.adapters.infra_adapter import LLMClient, EmbeddingClient, VectorDBClient
from source.ingestion_service.core.config.settings import AppSettings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("[LIFESPAN] startup initiated")

    # ---- Startup ----
    settings = AppSettings()

    llm_client = LLMClient(settings=settings)
    await llm_client.start()

    embedding_client = EmbeddingClient(settings=settings)
    await embedding_client.start()
    
    vector_db_client = VectorDBClient(settings=settings)
    await vector_db_client.start()

    app.state.llm_client = llm_client
    app.state.embedding_client = embedding_client
    app.state.vector_db_client = vector_db_client

    logger.info("[LIFESPAN] clients initialized")

    try:
        yield
    finally:
        # ---- Shutdown ----
        logger.info("[LIFESPAN] shutdown initiated")

        await llm_client.close()
        await embedding_client.close()
        await vector_db_client.close()

        logger.info("[LIFESPAN] shutdown completed")