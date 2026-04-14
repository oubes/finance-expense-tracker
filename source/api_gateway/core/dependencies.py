import logging
from functools import lru_cache
from fastapi import Depends

from source.api_gateway.core.settings import Settings
from source.api_gateway.clients.rag_client import RAGClient
from source.api_gateway.clients.ingestion_client import IngestionClient

# ---- Logger ----
logger = logging.getLogger(__name__)


# ------------- Settings (cached singleton) -------------
@lru_cache
def get_settings() -> Settings:
    logger.info("[DEPENDENCIES] loading settings (cached)")

    try:
        settings = Settings()
        logger.info("[DEPENDENCIES] settings loaded SUCCESS")
        return settings

    except Exception:
        logger.exception("[DEPENDENCIES] settings load FAILED")
        raise


# ------------- RAG Client -------------
def get_rag_client(
    settings: Settings = Depends(get_settings),
) -> RAGClient:

    logger.info("[DEPENDENCIES] creating RAG client")

    try:
        client = RAGClient(settings.RAG_SERVICE_URL)
        logger.info("[DEPENDENCIES] RAG client created SUCCESS")
        return client

    except Exception:
        logger.exception("[DEPENDENCIES] RAG client creation FAILED")
        raise


# ------------- Ingestion Client -------------
def get_ingestion_client(
    settings: Settings = Depends(get_settings),
) -> IngestionClient:

    logger.info("[DEPENDENCIES] creating ingestion client")

    try:
        client = IngestionClient(settings.INGESTION_SERVICE_URL)
        logger.info("[DEPENDENCIES] ingestion client created SUCCESS")
        return client

    except Exception:
        logger.exception("[DEPENDENCIES] ingestion client creation FAILED")
        raise