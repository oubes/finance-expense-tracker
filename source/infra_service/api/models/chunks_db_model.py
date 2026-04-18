from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class ChunkIn(BaseModel):

    content: str
    summary: str

    embedding: list[float] = Field(..., min_length=1024, max_length=1024)

    chunk_title: str
    doc_title: str
    source: str

    page: int
    total_pages: int

    created_at: datetime
    pipeline_version: str

    score: float