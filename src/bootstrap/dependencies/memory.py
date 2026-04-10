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
from src.services.db_services.queries.memory import user_facts_mem_queries

# ---- Services ----
from src.services.db_services.operations.memory.user_facts_mem_ops import UserFactsOps

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