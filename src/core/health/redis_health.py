import time
import asyncio
import redis.asyncio as redis
import logging
from src.bootstrap.dependencies import get_settings
from src.core.health.schemas.health_schemas import DependencyResult, RedisHealthData

logger = logging.getLogger(__name__)


async def check_redis(timeout: float = 1.0) -> DependencyResult:
    start = time.perf_counter()
    settings = get_settings()
    r_conf = settings.redis

    try:
        client = redis.from_url(r_conf.full_url, socket_timeout=timeout)

        async with asyncio.timeout(timeout):
            pong = await client.ping()

        latency = (time.perf_counter() - start) * 1000

        data = RedisHealthData(
            healthy=bool(pong),
            latency_ms=latency,
        )

        logger.info("Redis health check completed")

        return DependencyResult(
            status="success" if pong else "failed",
            data=data.model_dump(),
        )

    except Exception as e:
        logger.exception("Redis health check failed")

        return DependencyResult(
            status="failed",
            error=str(e),
        )