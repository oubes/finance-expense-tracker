import logging
from fastapi import Response, status

from src.bootstrap.dependencies import (
    get_settings,
    get_db_client,
    get_db_connection,
)
from src.core.health.schemas.health_schemas import DependencyResult

from core.health.app_health import get_app_health
from core.health.db_health import check_db
from core.health.redis_health import check_redis
from core.health.llm_health import LLMHealth
from core.health.embedder_health import EmbedderHealth
from core.health.cross_encoder_health import CrossEncoderHealth

logger = logging.getLogger(__name__)


async def get_readiness(response: Response) -> dict:
    logger.info("Aggregating system readiness results")

    settings = get_settings()

    db_conn_cm = get_db_connection()
    db_conn = await db_conn_cm.__anext__()
    db_client = get_db_client(db_conn)

    llm_health = LLMHealth()
    embedder_health = EmbedderHealth()
    cross_encoder_health = CrossEncoderHealth()

    dependencies: dict[str, DependencyResult] = {
        "app": await get_app_health(),
        "database": await check_db(db_client),
        "redis": await check_redis(),
        "llm": await llm_health.check(),
        "embedder": await embedder_health.check(),
        "cross_encoder": await cross_encoder_health.check(),
    }

    is_ready = all(dep.status == "success" for dep in dependencies.values())

    response.status_code = (
        status.HTTP_200_OK
        if is_ready
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    logger.info(f"Final readiness status: {'READY' if is_ready else 'NOT_READY'}")

    return {
        "status": "ready" if is_ready else "not_ready",
        "dependencies": {k: v.model_dump() for k, v in dependencies.items()},
    }