from fastapi import Depends
from functools import lru_cache
import logging

# ---- Settings ----
from source.infra_service.core.config.settings import AppSettings, get_config

# ---- Clients ----
from source.infra_service.adapters import LLMClient, EmbeddingClient, PostgresVectorClient

# ---- Services ----
from source.infra_service.application import LLMService, EmbeddingService, VectorDBService

# ---- Use Cases ----
from source.infra_service.application.use_cases.chunk_use_case import ChunkingUseCase
from source.infra_service.application.use_cases.semantic_mem_use_case import SemanticMemoryUseCase
from source.infra_service.application.use_cases.user_facts_mem_use_case import UserFactsUseCase
from source.infra_service.application.use_cases.transactions_mem_use_case import TransactionsUseCase

# ---- Queries ----
from source.infra_service.queries import (
    chunk_queries,
    semantic_memory_queries,
    user_facts_queries,
    transactions_queries
)

# ---- Logger ----
logger = logging.getLogger(__name__)


@lru_cache()
def get_settings():
    return get_config()

async def get_llm_client(settings: AppSettings = Depends(get_settings)):
    return LLMClient(settings)

async def get_embedding_client(settings: AppSettings = Depends(get_settings)):
    return EmbeddingClient(settings)

async def get_vector_db_client(settings: AppSettings = Depends(get_settings)):
    return PostgresVectorClient(settings)

async def get_llm_service(
    llm_client: LLMClient = Depends(get_llm_client),
    settings: AppSettings = Depends(get_settings)
):
    return LLMService(llm_client, settings=settings)

async def get_embedding_service(
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
    settings: AppSettings = Depends(get_settings)
):
    return EmbeddingService(embedding_client, settings=settings)

async def get_vector_db_service(
    vector_db_client: PostgresVectorClient = Depends(get_vector_db_client),
    settings: AppSettings = Depends(get_settings)
):
    return VectorDBService(client=vector_db_client, settings=settings)

async def get_chunking_use_case(
    vector_db_client: PostgresVectorClient = Depends(get_vector_db_client),
):
    return ChunkingUseCase(client=vector_db_client)

async def get_semantic_memory_use_case(
    vector_db_client: PostgresVectorClient = Depends(get_vector_db_client),
):
    return SemanticMemoryUseCase(
        db_client=vector_db_client,
        queries=semantic_memory_queries
    )

async def get_user_facts_use_case(
    vector_db_client: PostgresVectorClient = Depends(get_vector_db_client),
):
    return UserFactsUseCase(
        db_client=vector_db_client,
        queries=user_facts_queries
    )

async def get_transactions_use_case(
    vector_db_client: PostgresVectorClient = Depends(get_vector_db_client),
):
    return TransactionsUseCase(
        db_client=vector_db_client,
        queries=transactions_queries
    )


