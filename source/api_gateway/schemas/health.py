from pydantic import BaseModel
from typing import Literal, Optional


class ServiceHealthResponse(BaseModel):
    status: Literal["up", "down", "degraded", "unreachable"]
    service: str
    error: str | None = None