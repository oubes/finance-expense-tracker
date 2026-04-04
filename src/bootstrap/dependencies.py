# ---- Standard Library ----
import logging
from functools import lru_cache
from collections.abc import AsyncIterator

# ---- Core Config ----
from src.core.config.loader import load_settings
from src.core.config.settings import AppSettings

# ---- Infrastructure ----
from src.infrastructure.embeddings.model_loader import ModelLoader as EmbedModelLoader
from src.infrastructure.cross_encoder.model_loader import ModelLoader as CrossEncoderModelLoader
from src.infrastructure.cross_encoder.encoder import Encoder as CrossEncoder
from src.infrastructure.llm.model_loader import LLMClient

# ---- Vector DB ----
from src.infrastructure.vector_db.core.db_conn import DBConnect
from src.infrastructure.vector_db.core.db_client import PostgresVectorClient

# ---- Retrieval / RAG ----
from src.modules.retrieval.bm25_retrieval import BM25Retriever
from src.modules.retrieval.vector_retriever import VectorRetriever
from src.modules.retrieval.hybrid_retriever import HybridRetriever
from src.modules.retrieval.queries import VECTOR_SEARCH_QUERY, BM25_SEARCH_QUERY

logger = logging.getLogger(__name__)


# Core Config
@lru_cache()
def get_settings() -> AppSettings:
    logger.info("Loading application settings")
    return load_settings()


# LLM
@lru_cache()
def get_llm_client() -> LLMClient:
    logger.info("Initializing LLM Client")
    return LLMClient()


# Models (Singletons)
@lru_cache()
def get_embedding_model():
    logger.info("Loading embedding model")
    loader = EmbedModelLoader()
    return loader


@lru_cache()
def get_cross_encoder_model():
    logger.info("Loading cross encoder model")
    loader = CrossEncoderModelLoader()
    return loader


@lru_cache()
def get_cross_encoder() -> CrossEncoder:
    logger.info("Initializing Cross Encoder")
    model = get_cross_encoder_model()
    return CrossEncoder(model_loader=model)


# DB Lifecycle (Async)
async def get_db_connection() -> AsyncIterator[DBConnect]:
    logger.info("Creating async DB connection")
    conn = DBConnect()

    try:
        if hasattr(conn, "connect") and callable(conn.connect):
            result = conn.connect()
            if hasattr(result, "__await__"):
                await result

        yield conn

    finally:
        logger.info("Closing async DB connection")
        close_fn = getattr(conn, "close", None)
        if close_fn:
            result = close_fn()
            if hasattr(result, "__await__"):
                await result


# DB Client (Per Request)
def get_db_client(conn: DBConnect) -> PostgresVectorClient:
    logger.info("Creating DB client from connection")
    return PostgresVectorClient(conn=conn)


# Retrievers (Factory Pattern)
def get_bm25_retriever(db_client: PostgresVectorClient) -> BM25Retriever:
    logger.info("Initializing BM25 Retriever")
    return BM25Retriever(
        db_client=db_client,
        query_sql=BM25_SEARCH_QUERY,
    )


def get_vector_retriever(
    db_client: PostgresVectorClient,
    embedding_model,
) -> VectorRetriever:
    logger.info("Initializing Vector Retriever")

    return VectorRetriever(
        db_client=db_client,
        embedding_fn=embedding_model,
        query_sql=VECTOR_SEARCH_QUERY,
    )


def get_hybrid_retriever(
    bm25: BM25Retriever,
    vector: VectorRetriever,
) -> HybridRetriever:
    logger.info("Initializing Hybrid Retriever")

    return HybridRetriever(
        bm25=bm25,
        vector=vector,
    )


# Optional Composition Helpers
def build_retrievers(
    db_client: PostgresVectorClient,
    embedding_model,
):
    bm25 = get_bm25_retriever(db_client)
    vector = get_vector_retriever(db_client, embedding_model)

    hybrid = get_hybrid_retriever(bm25, vector)

    return {
        "bm25": bm25,
        "vector": vector,
        "hybrid": hybrid,
    }
