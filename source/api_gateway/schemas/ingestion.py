from pydantic import BaseModel
from typing import Literal, Any


class IngestResponse(BaseModel):
    status: Literal["success", "failed"]
    data: Any | None = None
    error: str | None = None