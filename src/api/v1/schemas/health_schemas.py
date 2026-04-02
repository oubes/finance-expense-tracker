from pydantic import BaseModel
from typing import Any

class DependencyResult(BaseModel):
    status: str  # "success" | "failed"
    data: dict[str, Any] | None = None
    error: str | None = None

class AppHealthData(BaseModel):
    status: str
    uptime_seconds: float
    started_at: float

class HealthResponse(BaseModel):
    status: str

class ReadinessResponse(BaseModel):
    status: str  # "ready" | "not_ready"
    dependencies: dict[str, DependencyResult]