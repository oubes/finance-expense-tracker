from fastapi import Depends
from functools import lru_cache
import logging

# ---- Settings ----
from source.infra_service.core.config.settings import AppSettings

# ---- Clients ----
from source.infra_service.adapters import LLMClient, EmbeddingClient, PostgresVectorClient

# ---- Services ----
from source.infra_service.application import LLMService, EmbeddingService, PostgresVectorClient

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

