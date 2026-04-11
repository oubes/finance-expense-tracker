# ---- Standard Library ----
import logging

# ---- FastAPI ----
from fastapi import Depends

# ---- Core Config ----
from src.core.config.settings import AppSettings
from src.bootstrap.dependencies.settings import get_settings

# ---- infrastructure ----
from src.bootstrap.dependencies.vector_db import get_db_client

# ---- queries ----
from src.services.db_services.queries.memory.long_term import user_facts_queries, analytics_queries, transactions_queries
from src.services.db_services.queries.memory.short_term import session_queries, conversation_queries, working_queries

# ---- Services ----
from src.services.db_services.operations.memory.long_term.user_facts_ops import UserFactsOps
from src.services.db_services.operations.memory.long_term.analytics_ops import AnalyticsOps
from src.services.db_services.operations.memory.long_term.transactions_ops import TransactionsOps
from src.services.db_services.operations.memory.long_term.tags_ops import TagsOps
from src.services.db_services.operations.memory.long_term.vector_ops import VectorOps
from src.services.db_services.operations.memory.short_term.session_state_ops import SessionOps
from src.services.db_services.operations.memory.short_term.conversation_ops import ConversationOps
from src.services.db_services.operations.memory.short_term.working_memory_ops import WorkingOps
from src.services.db_services.operations.memory.short_term.stm_buffer_ops import STMBufferOps

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- User Facts Memory Service ----
async def get_init_user_facts_table(
    settings: AppSettings = Depends(get_settings),
    db_client=Depends(get_db_client),
) -> UserFactsOps:
    logger.info("Initializing UserFactsOps")
    return UserFactsOps(
        db_client=db_client,
        queries=user_facts_mem_queries,
    )