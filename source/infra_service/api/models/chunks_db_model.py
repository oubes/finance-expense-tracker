# ---- Imports ----
from pydantic import BaseModel, Field
from datetime import datetime
import numpy as np
from uuid import UUID


# ---- Utility ----
def _random_embedding(dim: int = 1024) -> list[float]:
    return np.round(np.random.rand(dim), 4).tolist()


# -------------------- BASE MODELS --------------------

# ---- Base Chunk Structure ----
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
    chunk_score: float = 0.0
    bm25_score: float = 0.0
    vector_score: float = 0.0


# ---- Input Payload (Write) ----
class ChunkIn(ChunkBase):
    embedding: list[float] = Field(
        default_factory=_random_embedding,
        min_length=1024,
        max_length=1024,
        examples=[_random_embedding()],
    )


# ---- Output Payload (Read) ----
class ChunkOut(ChunkBase):
    id: UUID


# ---- Batch Insert Payload ----
class ChunkBatchIn(BaseModel):
    chunks: list[ChunkIn]


# -------------------- SEARCH MODELS --------------------

# ---- BM25 Search Input ----
class BM25SearchRequest(BaseModel):
    query: str = Field(default="python")
    limit: int = 10


# ---- Vector Search Input ----
class VectorSearchRequest(BaseModel):
    embedding: list[float] = Field(
        default_factory=_random_embedding,
        min_length=1024,
        max_length=1024,
        examples=[_random_embedding()],
    )
    limit: int = 10


# ---- Hybrid Search Input ----
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


# ---- Search Output ----
class SearchResponse(BaseModel):
    query: str | None = None
    count: int
    results: list[ChunkOut]


# -------------------- GET OPERATIONS MODELS --------------------

# ---- Count Result ----
class CountResponse(BaseModel):
    count: int
    message: str


# ---- Health Status ----
class HealthCheckResponse(BaseModel):
    message: str


# ---- Init Result ----
class InitTableResponse(BaseModel):
    message: str
    status: int


# ---- Single Chunk Fetch ----
class GetChunkByIdResponse(BaseModel):
    result: ChunkOut | None


# -------------------- POST OPERATIONS MODELS --------------------

# ---- Bulk Insert Request ----
class InsertChunksRequest(BaseModel):
    chunks: list[ChunkIn]


# ---- Bulk Insert Response ----
class InsertChunksResponse(BaseModel):
    message: str
    count: int


# ---- Page-Based Query Request ----
class GetChunksByPagesRequest(BaseModel):
    pages: list[int]


# ---- Page-Based Query Response ----
class GetChunksByPagesResponse(BaseModel):
    count: int
    results: list[ChunkOut]


# -------------------- PATCH OPERATIONS MODELS --------------------

# ---- Update Payload ----
class UpdateChunkRequest(BaseModel):
    data: ChunkIn


# ---- Update Result ----
class UpdateChunkResponse(BaseModel):
    message: str


# -------------------- DELETE OPERATIONS MODELS --------------------

# ---- Single Delete Result ----
class DeleteChunkResponse(BaseModel):
    success: bool


# ---- Bulk Delete Result ----
class DeleteChunksResponse(BaseModel):
    message: str


# ---- Drop Table Result ----
class DropTableResponse(BaseModel):
    message: str