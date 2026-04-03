import time
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AppHealth(BaseModel):
    status: str
    uptime_seconds: float
    started_at: float


_start_time = time.time()


def get_app_health() -> AppHealth:
    try:
        uptime = time.time() - _start_time

        result = AppHealth(
            status="running",
            uptime_seconds=uptime,
            started_at=_start_time,
        )

        logger.info(
            f"App health checked | uptime_seconds={uptime:.3f} | started_at={_start_time}"
        )

        return result

    except Exception as e:
        logger.exception("App health check failed")

        # fallback safe response (still valid schema)
        return AppHealth(
            status="error",
            uptime_seconds=0.0,
            started_at=_start_time,
        )