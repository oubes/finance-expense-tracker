import time
import asyncio
from pydantic import BaseModel
from psycopg import AsyncConnection

from src.core.config.settings import AppSettings


class DependencyStatus(BaseModel):
    healthy: bool
    detail: str
    latency_ms: float | None = None


async def check_db(settings: AppSettings, timeout: float = 2.0) -> DependencyStatus:
    start = time.perf_counter()

    db_settings = settings.database

    try:
        async with asyncio.timeout(timeout):
            conn = await AsyncConnection.connect(db_settings.full_url) # type: ignore

            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                await cur.fetchone()

            await conn.close()

        latency = (time.perf_counter() - start) * 1000

        return DependencyStatus(
            healthy=True,
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