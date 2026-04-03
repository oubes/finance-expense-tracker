import asyncio
import logging
from fastapi import Response, status

from src.core.config.loader import load_settings
from .app_health import get_app_health
from .db_health import check_db
from .redis_health import check_redis
from .llm_health import LLMHealth
from .embedder_health import EmbedderHealth

from src.api.v1.schemas.health_schemas import (
    DependencyResult,
    AppHealthData,
    DBHealthData,
    RedisHealthData,
    LLMHealthData,
    EmbedderHealthData,
)

logger = logging.getLogger(__name__)


# =========================
# Helpers
# =========================

async def _check_app(dependencies: dict) -> bool:
    try:
        app = get_app_health()

        dependencies["app"] = DependencyResult(
            status="success",
            data=AppHealthData(**app.model_dump()).model_dump(),
        )

        logger.info("App health check passed")
        return True

    except Exception as e:
        logger.exception("App health check failed")
        dependencies["app"] = DependencyResult(
            status="failed",
            error=str(e),
        )
        return False


async def _check_db(settings, dependencies: dict) -> bool:
    try:
        db_status = await check_db(settings)

        dependencies["database"] = DependencyResult(
            status="success" if db_status.healthy else "failed",
            data=DBHealthData(**db_status.model_dump()).model_dump(),
        )

        logger.info(f"DB health check: {db_status.healthy}")
        return db_status.healthy

    except Exception as e:
        logger.exception("DB health check failed")
        dependencies["database"] = DependencyResult(
            status="failed",
            error=str(e),
        )
        return False


async def _check_redis(settings, dependencies: dict) -> bool:
    try:
        redis_status = await check_redis(settings)

        dependencies["redis"] = DependencyResult(
            status="success" if redis_status.healthy else "failed",
            data=RedisHealthData(**redis_status.model_dump()).model_dump(),
        )

        logger.info(f"Redis health check: {redis_status.healthy}")
        return redis_status.healthy

    except Exception as e:
        logger.exception("Redis health check failed")
        dependencies["redis"] = DependencyResult(
            status="failed",
            error=str(e),
        )
        return False


async def _check_llm(dependencies: dict) -> bool:
    try:
        llm_health = LLMHealth()
        llm_status = await llm_health.check()

        dependencies["llm"] = DependencyResult(
            status="success" if llm_status.healthy else "failed",
            data=LLMHealthData(**llm_status.model_dump()).model_dump() if llm_status.healthy else None,
            error=None if llm_status.healthy else llm_status.detail,
        )

        logger.info(f"LLM health check: {llm_status.healthy}")
        return llm_status.healthy

    except Exception as e:
        logger.exception("LLM health check failed")
        dependencies["llm"] = DependencyResult(
            status="failed",
            error=str(e),
        )
        return False


async def _check_embedder(dependencies: dict) -> bool:
    try:
        embedder_health = EmbedderHealth()
        embedder_status = await embedder_health.check()

        dependencies["embedder"] = DependencyResult(
            status="success" if embedder_status["healthy"] else "failed",
            data=EmbedderHealthData(**embedder_status).model_dump()
            if embedder_status["healthy"]
            else None,
            error=None if embedder_status["healthy"] else embedder_status.get("error"),
        )

        logger.info(f"Embedder health check: {embedder_status['healthy']}")
        return embedder_status["healthy"]

    except Exception as e:
        logger.exception("Embedder health check failed")
        dependencies["embedder"] = DependencyResult(
            status="failed",
            error=str(e),
        )
        return False


# =========================
# Orchestrator
# =========================

async def get_readiness(response: Response):
    logger.info("Starting readiness check")

    settings = load_settings()
    dependencies: dict[str, DependencyResult] = {}

    app_ok = await _check_app(dependencies)
    db_ok = await _check_db(settings, dependencies)
    redis_ok = await _check_redis(settings, dependencies)
    llm_ok = await _check_llm(dependencies)
    embedder_ok = await _check_embedder(dependencies)

    all_ok = app_ok and db_ok and redis_ok and llm_ok and embedder_ok

    response.status_code = (
        status.HTTP_200_OK
        if all_ok
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    logger.info(f"Readiness check completed. Status: {'ready' if all_ok else 'not_ready'}")

    return {
        "status": "ready" if all_ok else "not_ready",
        "dependencies": dependencies,
    }