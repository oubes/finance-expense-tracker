# ---- Imports ----
import time
import asyncio
import logging
from src.core.schemas.health.health_schemas import DependencyResult, DBHealthData
from src.bootstrap.dependencies.vector_db_dep import get_settings, get_db_client

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)


# ---- Database Health Check ----
async def check_db(timeout: float = 2.0) -> DependencyResult:
    # ---- Start Timer ----
    start = time.perf_counter()

    # ---- Load Settings ----
    settings = get_settings()

    # ---- Resolve DB Client ----
    db_client = await get_db_client()

    try:
        # ---- Timeout Guard ----
        async with asyncio.timeout(timeout):

            # ---- Execute Health Query ----
            await db_client.execute("SELECT 1", fetch=True)

        # ---- Latency Calculation ----
        latency = (time.perf_counter() - start) * 1000

        # ---- Health Data Construction ----
        data = DBHealthData(
            healthy=True,
            latency_ms=round(latency, 3),
            db_type=settings.database.type,  # type: ignore
            db_name=settings.database.db,  # type: ignore
        )

        # ---- Success Logging ----
        logger.info(f"DB health check successful | latency: {latency:.2f}ms")

        # ---- Success Response ----
        return DependencyResult(
            status="success",
            data=data.model_dump(),
        )

    except Exception as e:
        # ---- Error Logging ----
        logger.exception("DB health check failed")

        # ---- Failure Response ----
        return DependencyResult(
            status="failed",
            error=str(e),
        )

    finally:
        # ---- Cleanup Resources ----
        try:
            await db_client.close()
        except Exception:
            logger.exception("Failed to close DB client")