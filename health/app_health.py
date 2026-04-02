import time
from pydantic import BaseModel


class AppHealth(BaseModel):
    status: str
    uptime_seconds: float
    started_at: float


_start_time = time.time()


def get_app_health() -> AppHealth:
    uptime = time.time() - _start_time

    return AppHealth(
        status="running",
        uptime_seconds=uptime,
        started_at=_start_time,
    )