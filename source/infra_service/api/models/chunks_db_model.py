# ---- Imports ----
from pydantic import BaseModel, Field
from datetime import datetime
import numpy as np
from uuid import UUID

# ---- Utility ----
def _random_embedding(dim: int = 1024) -> list[float]:
    return np.round(np.random.rand(dim), 4).tolist()

# ---- Chunk Models ----
class ChunkBase(BaseModel):
    content: str
    summary: str
    chunk_title: str
    doc_title: str
    source: str
    page: int
    total_pages: int
    created_at: datetime
    pipeline_version: str
    score: float = 0.0

class ChunkIn(ChunkBase):
    embedding: list[float] = Field(
        default_factory=_random_embedding,
        min_length=1024,
        max_length=1024,
        examples=[_random_embedding()],
    )

class ChunkOut(ChunkBase):
    id: UUID

class ChunkBatchIn(BaseModel):
    chunks: list[ChunkIn]

# ---- Search Request/Response Models ----
class BM25SearchRequest(BaseModel):
    query: str = Field(default="python")
    limit: int = 10

class VectorSearchRequest(BaseModel):
    embedding: list[float] = Field(
        default_factory=_random_embedding,
        min_length=1024,
        max_length=1024,
        examples=[_random_embedding()],
    )
    limit: int = 10

class HybridSearchRequest(BaseModel):
    query: str = Field(default="python")
    embedding: list[float] = Field(
        default_factory=_random_embedding,
        min_length=1024,
        max_length=1024,
        examples=[_random_embedding()],
    )
    limit: int = 10
    weights: dict = Field(
        default_factory=lambda: {"bm25": 0.4, "vector": 0.6},
    )

class SearchResponse(BaseModel):
    query: str | None = None
    count: int
    results: list[ChunkOut]

class CountResponse(BaseModel):
    count: int
    message: str

# ---- Route Request/Response Models ----
class HealthCheckResponse(BaseModel):
    message: str

class InitTableResponse(BaseModel):
    message: str
    status: int

class DeleteChunksResponse(BaseModel):
    message: str

class DropTableResponse(BaseModel):
    message: str

class InsertChunksRequest(BaseModel):
    chunks: list[ChunkIn]

class InsertChunksResponse(BaseModel):
    message: str
    count: int