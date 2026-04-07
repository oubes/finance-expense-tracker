# ---- Imports ----
import time
import logging
from src.core.schemas.health.health_schemas import DependencyResult, AppHealthData

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)

# ---- Application Start Time ----
_start_time = time.time()


# ---- App Health Check ----
async def get_app_health() -> DependencyResult:
    try:
        uptime = time.time() - _start_time
        
        # ---- Health Data Construction ----
        data = AppHealthData(
            status="running",
            uptime_seconds=round(uptime, 3),
            started_at=round(_start_time, 3),
        )

        logger.info("App health check passed")

        # ---- Success Response ----
        return DependencyResult(
            status="success",
            data=data.model_dump(),
        )

    except Exception as e:
        logger.exception("App health check failed")

        # ---- Failure Response ----
        return DependencyResult(
            status="failed",
            error=str(e),
        )