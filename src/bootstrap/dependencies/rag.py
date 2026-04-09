# ---- Standard Library ----
import logging

# ---- FastAPI ----
from fastapi import Depends

# ---- Infrastructure ----
from src.bootstrap.dependencies.llm import get_llm_generator
from src.infrastructure.llm.llm_generator import LLMGenerator
from src.infrastructure.vector_db.core.db_client import PostgresVectorClient
from src.bootstrap.dependencies.vector_db import get_db_client
from src.bootstrap.dependencies.embeddings import get_embedding_model

# ---- Retrieval ----
from src.modules.rag.retrieval.bm25_retrieval import BM25Retriever
from src.modules.rag.retrieval.vector_retriever import VectorRetriever
from src.modules.rag.retrieval.hybrid_retriever import HybridRetriever
from src.modules.rag.retrieval.queries import VECTOR_SEARCH_QUERY, BM25_SEARCH_QUERY
from src.bootstrap.dependencies.prompting import get_msg_builder, get_llm_json_extractor, get_llm_json_validator
from src.modules.prompts.processing.llm_json_extractor import LLMJsonExtractor
from src.modules.prompts.processing.llm_json_validator import LLMJsonValidator

# ---- Pipeline ----
from src.pipelines.v1.aug_gen_pipeline import AugGenPipeline

# ---- Workflow ----
from src.workflow.rag_workflow import RAGWorkflow

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


# ---- AugGen Pipeline ----
def get_aug_gen_pipeline(
    msg_builder = Depends(get_msg_builder),
    generator: LLMGenerator = Depends(get_llm_generator),
    extractor: LLMJsonExtractor = Depends(get_llm_json_extractor),
    validator: LLMJsonValidator = Depends(get_llm_json_validator)
) -> AugGenPipeline:
    logger.info("Initializing AugGen Pipeline")
    return AugGenPipeline(
        msg_builder=msg_builder,
        generator=generator,
        extractor=extractor,
        validator=validator
    )

# ---- RAG Workflow ----
def get_rag_workflow(
    aug_gen_pipeline: AugGenPipeline = Depends(get_aug_gen_pipeline)
) -> RAGWorkflow:
    logger.info("Initializing RAG Workflow")
    return RAGWorkflow(aug_gen_pipeline=aug_gen_pipeline)