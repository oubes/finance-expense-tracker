# ---- Imports ----
import logging
from fastapi import Response, status

from src.bootstrap.dependencies import (
    get_settings,
    get_db_client,
)

from src.core.health.schemas.health_schemas import DependencyResult

from src.core.health.app_health import get_app_health
from src.core.health.db_health import check_db
from src.core.health.redis_health import check_redis
from src.core.health.llm_health import LLMHealth
from src.core.health.embedder_health import EmbedderHealth
from src.core.health.cross_encoder_health import CrossEncoderHealth

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Readiness Handler ----
async def get_readiness(response: Response) -> dict:
    # ---- Aggregation Start ----
    logger.info("Aggregating system readiness results")

    # ---- Settings Initialization ----
    settings = get_settings()

    # ---- DB Client Resolution ----
    db_client = await get_db_client()

    # ---- Health Check Components ----
    llm_health = LLMHealth()
    embedder_health = EmbedderHealth()
    cross_encoder_health = CrossEncoderHealth()

    # ---- Dependency Checks Aggregation ----
    dependencies: dict[str, DependencyResult] = {
        "app": await get_app_health(),
        "database": await check_db(),
        "redis": await check_redis(),
        "llm": await llm_health.check(),
        "embedder": await embedder_health.check(),
        "cross_encoder": await cross_encoder_health.check(),
    }

    # ---- Readiness Evaluation ----
    is_ready = all(dep.status == "success" for dep in dependencies.values())

    # ---- HTTP Status Assignment ----
    response.status_code = (
        status.HTTP_200_OK
        if is_ready
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    # ---- Final Logging ----
    logger.info(f"Final readiness status: {'READY' if is_ready else 'NOT_READY'}")

    # ---- Response Construction ----
    return {
        "status": "ready" if is_ready else "not_ready",
        "dependencies": {k: v.model_dump() for k, v in dependencies.items()},
    }