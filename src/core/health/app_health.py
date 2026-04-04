import time
import logging
from src.core.health.schemas.health_schemas import DependencyResult, AppHealthData

# Initialize logger
logger = logging.getLogger(__name__)

# Track application start time
_start_time = time.time()

async def get_app_health() -> DependencyResult:
    """
    Calculate application uptime and status.
    """
    try:
        uptime = time.time() - _start_time
        
        data = AppHealthData(
            status="running",
            uptime_seconds=uptime,
            started_at=_start_time,
        )

        logger.info("App health check passed")
        return DependencyResult(
            status="success",
            data=data.model_dump(),
        )

    except Exception as e:
        logger.exception("App health check failed")
        return DependencyResult(
            status="failed",
            error=str(e),
        )