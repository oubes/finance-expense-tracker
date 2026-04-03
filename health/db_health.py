import time
import asyncio
import logging
from pydantic import BaseModel
from psycopg import AsyncConnection

from src.core.config.settings import AppSettings

logger = logging.getLogger(__name__)


class DependencyStatus(BaseModel):
    healthy: bool
    detail: str
    latency_ms: float | None = None


async def check_db(settings: AppSettings, timeout: float = 2.0) -> DependencyStatus:
    start = time.perf_counter()

    db_settings = settings.database

    logger.info("Starting DB health check")

    try:
        async with asyncio.timeout(timeout):
            conn = await AsyncConnection.connect(db_settings.full_url)  # type: ignore

            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                await cur.fetchone()

            await conn.close()

        latency = (time.perf_counter() - start) * 1000

        result = DependencyStatus(
            healthy=True,
            detail="ok",
            latency_ms=latency,
        )

        logger.info(f"DB health check successful | latency_ms={latency:.2f}")
        return result

    except Exception as e:
        latency = (time.perf_counter() - start) * 1000

        logger.exception(f"DB health check failed | latency_ms={latency:.2f}")

        return DependencyStatus(
            healthy=False,
            detail=str(e),
            latency_ms=latency,
        )