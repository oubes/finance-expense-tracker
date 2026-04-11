# ---- Standard Library ----
import logging
from functools import lru_cache

# ---- FastAPI ----
from fastapi import Depends

# ---- Core Config ----
from src.core.config.settings import AppSettings
from src.bootstrap.dependencies.settings import get_settings

# ---- Infrastructure ----
from src.bootstrap.dependencies.vector_db import get_db_client

# ---- Operations ----
from src.services.memory.working.operations.stm_buffer_ops import STMBufferOps
from src.services.memory.working.operations.session_state_ops import SessionStateOps
from src.services.memory.working.operations.working_memory_ops import WorkingMemoryOps

from src.services.memory.analytical.operations.analytics_ops import AnalyticsOps
from src.services.memory.analytical.operations.transactions_ops import TransactionsOps

from src.services.memory.conversational.operations.conversation_ops import ConversationOps

from src.services.memory.semantic.operations.tags_ops import TagsOps
from src.services.memory.semantic.operations.vector_ops import VectorOps
from src.services.memory.semantic.operations.user_facts_ops import UserFactsOps

# ---- Queries ----
from src.services.memory.working.queries import (
    stm_buffer_queries,
    session_queries,
    working_queries,
)

from src.services.memory.analytical.queries import (
    analytics_queries,
    transactions_queries,
)

from src.services.memory.conversational.queries import conversation_queries

from src.services.memory.semantic.queries import (
    tags_queries,
    vector_queries,
    user_facts_queries,
)

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- DB Client Cache ----
@lru_cache()
def get_cached_db_client():
    return get_db_client()


# ---- STM Buffer Service ----
@lru_cache()
def get_stm_buffer_service() -> STMBufferOps:
    return STMBufferOps(
        db_client=get_cached_db_client(),
        queries=stm_buffer_queries,
    )


# ---- Session State Service ----
@lru_cache()
def get_session_state_service() -> SessionStateOps:
    return SessionStateOps(
        db_client=get_cached_db_client(),
        queries=session_queries,
    )


# ---- Working Memory Service ----
@lru_cache()
def get_working_memory_service() -> WorkingMemoryOps:
    return WorkingMemoryOps(
        db_client=get_cached_db_client(),
        queries=working_queries,
    )


# ---- Conversation Service ----
@lru_cache()
def get_conversation_service() -> ConversationOps:
    return ConversationOps(
        db_client=get_cached_db_client(),
        queries=conversation_queries,
    )


# ---- Analytics Service ----
@lru_cache()
def get_analytics_service() -> AnalyticsOps:
    return AnalyticsOps(
        db_client=get_cached_db_client(),
        queries=analytics_queries,
    )


# ---- Transactions Service ----
@lru_cache()
def get_transactions_service() -> TransactionsOps:
    return TransactionsOps(
        db_client=get_cached_db_client(),
        queries=transactions_queries,
    )


# ---- Tags Service ----
@lru_cache()
def get_tags_service() -> TagsOps:
    return TagsOps(
        db_client=get_cached_db_client(),
        queries=tags_queries,
    )


# ---- Vector Service ----
@lru_cache()
def get_vector_service() -> VectorOps:
    return VectorOps(
        db_client=get_cached_db_client(),
        queries=vector_queries,
    )


# ---- User Facts Service ----
@lru_cache()
def get_user_facts_service() -> UserFactsOps:
    return UserFactsOps(
        db_client=get_cached_db_client(),
        queries=user_facts_queries,
    )