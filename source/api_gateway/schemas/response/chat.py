from pydantic import BaseModel
from typing import Literal, Any

class ChatResponse(BaseModel):
    status: Literal["up", "degraded", "down", "unreachable"]
    data: Any | None = None
    error: str | None = None
    latency_ms: float | None