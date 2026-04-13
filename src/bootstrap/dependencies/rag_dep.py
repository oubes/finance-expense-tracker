# ---- Standard Library ----
import logging

# ---- FastAPI ----
from fastapi import Depends

# ---- Infrastructure ----
from src.services.llm_services.safe_generator import SafeGenerator

# ---- Prompting ----
from src.bootstrap.dependencies.prompting_dep import get_safe_generator

# ---- Embedding ----
from src.bootstrap.dependencies.embeddings_dep import get_embedding

# ---- Memory ----
from src.bootstrap.dependencies.memory_dep import (
    get_semantic_memory_service,
    get_transactions_service,
    get_user_facts_service,
)

# ---- Retrieval ----
from src.bootstrap.dependencies.vector_db_dep import (
    get_bm25_retriever,
    get_vector_retriever,
    get_reranker,
)

# ---- Services ----
from src.services.retrieve.operations.hybrid_retriever import HybridRetriever

# ---- Workflow ----
from src.workflow.rag_workflow import RAGWorkflow

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Hybrid Retriever ----
def get_hybrid_retriever(
    bm25=Depends(get_bm25_retriever),
    vector=Depends(get_vector_retriever),
    reranker=Depends(get_reranker),
) -> HybridRetriever:
    logger.info("Initializing Hybrid Retriever")

    return HybridRetriever(
        bm25_retriever=bm25,
        vector_retriever=vector,
        reranker=reranker,
    )

# ---- RAG Workflow ----
def get_rag_workflow(
    hybrid_retriever: HybridRetriever = Depends(get_hybrid_retriever),
    safe_generator: SafeGenerator = Depends(get_safe_generator),
    embedder=Depends(get_embedding),
    semantic_memory=Depends(get_semantic_memory_service),
    user_facts_memory=Depends(get_user_facts_service),
    transactions_memory=Depends(get_transactions_service),
) -> RAGWorkflow:
    logger.info("Initializing RAG Workflow")

    return RAGWorkflow(
        hybrid_retriever=hybrid_retriever,
        safe_generator=safe_generator,
        embedder=embedder,
        semantic_memory=semantic_memory,
        user_facts_memory=user_facts_memory,
        transactions_memory=transactions_memory,
    )