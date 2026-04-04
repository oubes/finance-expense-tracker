import logging
from fastapi import Response, status, Request

from src.core.config.loader import load_settings
from src.api.v1.schemas.health_schemas import DependencyResult

from health.app_health import get_app_health
from health.db_health import check_db
from health.redis_health import check_redis
from health.llm_health import LLMHealth
from health.embedder_health import EmbedderHealth
from health.cross_encoder_health import CrossEncoderHealth

logger = logging.getLogger(__name__)


async def get_readiness(request: Request, response: Response) -> dict:
    logger.info("Aggregating system readiness results")

    settings = load_settings()
    db_client = request.app.state.db_client

    dependencies: dict[str, DependencyResult] = {
        "app": await get_app_health(),

        "database": await check_db(db_client, settings),
        "redis": await check_redis(settings),
        "llm": await LLMHealth().check(),
        "embedder": await EmbedderHealth().check(),
        "cross_encoder": await CrossEncoderHealth().check(),
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
        "dependencies": dependencies,
    }