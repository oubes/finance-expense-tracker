# ---- Standard Library ----
import logging

# ---- FastAPI ----
from fastapi import Depends

# ---- Infrastructure ----
from src.infrastructure.vector_db.core.db_client import PostgresVectorClient
from src.bootstrap.dependencies.vector_db import get_db_client
from src.bootstrap.dependencies.embeddings import get_embedding_model

# ---- Retrieval ----
from src.modules.rag.retrieval.bm25_retrieval import BM25Retriever
from src.modules.rag.retrieval.vector_retriever import VectorRetriever
from src.modules.rag.retrieval.hybrid_retriever import HybridRetriever
from src.modules.rag.retrieval.queries import VECTOR_SEARCH_QUERY, BM25_SEARCH_QUERY

logger = logging.getLogger(__name__)


# ---- BM25 Retriever ----
def get_bm25_retriever(db_client: PostgresVectorClient = Depends(get_db_client)) -> BM25Retriever:
    logger.info("Initializing BM25 Retriever")
    return BM25Retriever(db_client=db_client, query_sql=BM25_SEARCH_QUERY)


# ---- Vector Retriever ----
def get_vector_retriever(
    db_client: PostgresVectorClient = Depends(get_db_client),
    embedding_model=Depends(get_embedding_model),
) -> VectorRetriever:
    logger.info("Initializing Vector Retriever")
    return VectorRetriever(
        db_client=db_client,
        embedding_fn=embedding_model,
        query_sql=VECTOR_SEARCH_QUERY,
    )


# ---- Hybrid Retriever ----
def get_hybrid_retriever(
    bm25: BM25Retriever = Depends(get_bm25_retriever),
    vector: VectorRetriever = Depends(get_vector_retriever),
) -> HybridRetriever:
    logger.info("Initializing Hybrid Retriever")
    return HybridRetriever(bm25=bm25, vector=vector)