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
from src.bootstrap.dependencies.prompting import get_msg_builder, get_llm_json_extractor, get_llm_json_validator
from src.modules.prompts.processing.llm_json_extractor import LLMJsonExtractor
from src.modules.prompts.processing.llm_json_validator import LLMJsonValidator
from src.bootstrap.dependencies.vector_db import get_bm25_retriever, get_vector_retriever, get_reranker

# ---- Services ----
from src.services.db_services.operations.hybrid_ret import HybridRetriever

# ---- Pipeline ----
from src.pipelines.v1.aug_gen_pipeline import AugGenPipeline

# ---- Workflow ----
from src.workflow.rag_workflow import RAGWorkflow

# ---- Logger ----
logger = logging.getLogger(__name__)

# ---- Hybrid Retriever ----
def get_hybrid_retriever(
    bm25 = Depends(get_bm25_retriever),
    vector = Depends(get_vector_retriever),
    reranker = Depends(get_reranker)
) -> HybridRetriever:
    logger.info("Initializing Hybrid Retriever")
    return HybridRetriever(bm25_retriever=bm25, vector_retriever=vector, reranker=reranker)


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
    aug_gen_pipeline: AugGenPipeline = Depends(get_aug_gen_pipeline),
    hybrid_retriever: HybridRetriever = Depends(get_hybrid_retriever)
) -> RAGWorkflow:
    logger.info("Initializing RAG Workflow")
    return RAGWorkflow(aug_gen_pipeline=aug_gen_pipeline, hybrid_retriever=hybrid_retriever)