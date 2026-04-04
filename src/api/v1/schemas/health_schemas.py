from pydantic import BaseModel, Field


# ---------- Dependency Result ----------
class DependencyResult(BaseModel):
    status: str  # "success" | "failed"
    data: dict | None = None
    error: str | None = None


# ---------- Generic Dependency Status ----------
class DependencyStatus(BaseModel):
    healthy: bool
    detail: str
    latency_ms: float | None = None
    model: str | None = None


# ---------- App Health ----------
class AppHealthData(BaseModel):
    status: str
    uptime_seconds: float = Field(..., ge=0)
    started_at: float


# ---------- DB Health ----------
class DBHealthData(BaseModel):
    healthy: bool
    latency_ms: float | None = None


# ---------- Redis Health ----------
class RedisHealthData(BaseModel):
    healthy: bool
    latency_ms: float | None = None


# ---------- LLM Health ----------
class LLMHealthData(BaseModel):
    healthy: bool
    model: str | None = None
    latency_ms: float | None = None


# ---------- Embedder Health ----------
class EmbedderHealthData(BaseModel):
    healthy: bool
    model: str | None = None
    dimension: int | None = None
    latency_ms: float | None = None


# ---------- Cross Encoder Health ----------
class CrossEncoderHealthData(BaseModel):
    healthy: bool
    model: str | None = None
    latency_ms: float | None = None


# ---------- Responses ----------
class HealthResponse(BaseModel):
    status: str  # "alive"


class ReadinessResponse(BaseModel):
    status: str  # "ready" | "not_ready"
    dependencies: dict[str, DependencyResult]