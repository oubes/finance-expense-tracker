import time
import asyncio
import redis.asyncio as redis
from pydantic import BaseModel

from src.core.config.settings import AppSettings


class DependencyStatus(BaseModel):
    healthy: bool
    detail: str
    latency_ms: float | None = None


async def check_redis(settings: AppSettings, timeout: float = 1.0) -> DependencyStatus:
    start = time.perf_counter()

    r_conf = settings.redis

    try:
        client = redis.from_url(r_conf.full_url, socket_timeout=timeout)

        async with asyncio.timeout(timeout):
            pong = await client.ping()

        latency = (time.perf_counter() - start) * 1000

        return DependencyStatus(
            healthy=bool(pong),
            detail="ok",
            latency_ms=latency,
        )

    except Exception as e:
        latency = (time.perf_counter() - start) * 1000

        return DependencyStatus(
            healthy=False,
            detail=str(e),
            latency_ms=latency,
        )