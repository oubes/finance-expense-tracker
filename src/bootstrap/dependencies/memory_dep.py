# ---- Standard Library ----
import logging

# ---- FastAPI ----
from fastapi import Depends

# ---- Core Config ----
from src.core.config.settings import AppSettings
from src.bootstrap.dependencies.settings_dep import get_settings

# ---- Infrastructure ----
from src.bootstrap.dependencies.vector_db_dep import get_db_client
from src.bootstrap.dependencies.prompting_dep import get_safe_generator
from src.bootstrap.dependencies.embeddings_dep import get_embedding

# ---- Operations ----
from src.services.memory.analytical.operations.analytics_ops import AnalyticsOps
from src.services.memory.analytical.operations.transactions_ops import TransactionsOps

from src.services.memory.semantic.operations.semantic_memory_ops import SemanticMemoryOps

from src.services.memory.semantic.operations.vector_ops import VectorOps
from src.services.memory.semantic.operations.user_facts_ops import UserFactsOps

# ---- Queries ----

from src.services.memory.semantic.queries import semantic_memory_queries
from src.services.memory.analytical.queries import (
    analytics_queries,
    transactions_queries,
)

from src.services.memory.conversational.queries import conversation_queries

from src.services.memory.semantic.queries import (
    vector_queries,
    user_facts_queries,
)

# ---- Pipelines ----
from src.pipelines.v1.conv_memory_pipeline import MemorySystem
from src.pipelines.v1.memory_pipeline import MemoryPipeline

# ---- Logger ----
logger = logging.getLogger(__name__)

# ---- DB CLIENT ----
def get_db_client_dep(db=Depends(get_db_client)):
    return db

# ---- SETTINGS ----
def get_settings_dep(settings: AppSettings = Depends(get_settings)):
    return settings

# ---- OTHER MEMORY OPS ----

def get_semantic_memory_service(db=Depends(get_db_client_dep)) -> SemanticMemoryOps:
    return SemanticMemoryOps(
        db_client=db,
        queries=semantic_memory_queries,
    )

def get_analytics_service(db=Depends(get_db_client_dep)) -> AnalyticsOps:
    return AnalyticsOps(
        db_client=db,
        queries=analytics_queries,
    )

def get_transactions_service(db=Depends(get_db_client_dep)) -> TransactionsOps:
    return TransactionsOps(
        db_client=db,
        queries=transactions_queries,
    )

def get_vector_service(db=Depends(get_db_client_dep)) -> VectorOps:
    return VectorOps(
        db_client=db,
        queries=vector_queries,
    )

def get_user_facts_service(db=Depends(get_db_client_dep)) -> UserFactsOps:
    return UserFactsOps(
        db_client=db,
        queries=user_facts_queries,
    )

# ---- MEMORY SYSTEM BUILDERS ----
    
def get_memory_pipeline(
    semantic_memory_operations: SemanticMemoryOps = Depends(get_semantic_memory_service),
    transactions_operations: TransactionsOps = Depends(get_transactions_service),
    user_facts_operations: UserFactsOps = Depends(get_user_facts_service),
    safe_generator=Depends(get_safe_generator),
    embedder=Depends(get_embedding)
):
    return MemoryPipeline(
        transactions_ops=transactions_operations,
        semantic_memory_ops=semantic_memory_operations,
        user_facts_ops=user_facts_operations,
        safe_generator=safe_generator,
        embedder=embedder
    )