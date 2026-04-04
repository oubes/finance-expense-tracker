import time
import asyncio
import logging
from src.bootstrap.dependencies import get_settings
from src.api.v1.schemas.health_schemas import DependencyResult, DBHealthData

logger = logging.getLogger(__name__)


async def check_db(db_client, timeout: float = 2.0) -> DependencyResult:
    start = time.perf_counter()
    settings = get_settings()

    try:
        async with asyncio.timeout(timeout):
            conn = db_client.db.conn

            if conn is None:
                raise RuntimeError("Database connection is not initialized")

            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                await cur.fetchone()

        latency = (time.perf_counter() - start) * 1000

        data = DBHealthData(
            healthy=True,
            latency_ms=latency,
            db_type=settings.database.type, # type: ignore
            db_name=settings.database.db, # type: ignore
        )

        logger.info(f"DB health check successful | latency: {latency:.2f}ms")

        return DependencyResult(
            status="success",
            data=data.model_dump(),
        )

    except Exception as e:
        logger.exception("DB health check failed")

        return DependencyResult(
            status="failed",
            error=str(e),
        )