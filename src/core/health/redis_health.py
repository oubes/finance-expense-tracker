# ---- Imports ----
import time
import asyncio
import redis.asyncio as redis
import logging
from src.bootstrap.dependencies import get_settings
from src.core.health.schemas.health_schemas import DependencyResult, RedisHealthData

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)


# ---- Redis Health Check ----
async def check_redis(timeout: float = 1.0) -> DependencyResult:
    start = time.perf_counter()
    settings = get_settings()
    r_conf = settings.redis

    try:
        # ---- Redis Client Initialization ----
        client = redis.from_url(r_conf.full_url, socket_timeout=timeout)

        # ---- Ping Execution ----
        async with asyncio.timeout(timeout):
            pong = await client.ping()

        latency = (time.perf_counter() - start) * 1000

        # ---- Health Data Construction ----
        data = RedisHealthData(
            healthy=bool(pong),
            latency_ms=round(latency, 3),
        )

        logger.info("Redis health check completed")

        # ---- Response ----
        return DependencyResult(
            status="success" if pong else "failed",
            data=data.model_dump(),
        )

    except Exception as e:
        logger.exception("Redis health check failed")

        # ---- Failure Response ----
        return DependencyResult(
            status="failed",
            error=str(e),
        )