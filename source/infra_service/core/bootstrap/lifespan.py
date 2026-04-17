# ---- Imports ----
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from source.infra_service.adapters import LLMClient, EmbeddingClient, PostgresVectorClient
from source.infra_service.core.config.settings import get_config

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("[LIFESPAN] startup initiated")

    settings = get_config()

    # ---- infra clients ----
    llm_client = LLMClient(settings)
    embedding_client = EmbeddingClient(settings)

    vector_db_client = PostgresVectorClient(settings)

    # ---- attach ----
    app.state.llm_client = llm_client
    app.state.embedding_client = embedding_client
    app.state.vector_db_client = vector_db_client

    logger.info("[LIFESPAN] infra initialized")

    try:
        yield

    finally:
        logger.info("[LIFESPAN] shutdown completed")