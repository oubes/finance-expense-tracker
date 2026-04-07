from pydantic import BaseModel
from typing import Any


# ---- Generic Wrapper ----
class DependencyResult(BaseModel):
    status: str
    data: Any | None = None
    error: str | None = None


# ---- App ----
class AppHealthData(BaseModel):
    status: str
    uptime_seconds: float
    started_at: float


# ---- DB ----
class DBHealthData(BaseModel):
    healthy: bool
    latency_ms: float
    db_type: str | None = None
    db_name: str | None = None


# ---- Redis ----
class RedisHealthData(BaseModel):
    healthy: bool
    latency_ms: float


# ---- LLM ----
class LLMHealthData(BaseModel):
    healthy: bool
    latency_ms: float
    model: str | None = None


# ---- Embedder ----
class EmbedderHealthData(BaseModel):
    healthy: bool
    latency_ms: float
    model: str | None = None
    dimension: int | None = None


# ---- Cross Encoder ----
class CrossEncoderHealthData(BaseModel):
    healthy: bool
    latency_ms: float
    model: str | None = None
    device: str | None = None