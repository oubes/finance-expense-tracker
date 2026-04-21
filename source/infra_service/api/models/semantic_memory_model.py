# ---- Imports ----
from pydantic import BaseModel, Field
import numpy as np


# ---- Embedding ----
def _random_embedding(dim: int = 1024):
    return np.round(np.random.rand(dim), 4).tolist()


# ---- BASE ----
class MemoryBase(BaseModel):
    user_id: str
    session_id: str
    role: str
    content: str


# ---- ADD MESSAGE ----
class AddMessageRequest(MemoryBase):
    embedding: list[float] = Field(default_factory=_random_embedding)


# ---- HISTORY ----
class HistoryRequest(BaseModel):
    user_id: str
    session_id: str


# ---- STM ----
class STMRequest(BaseModel):
    user_id: str
    session_id: str
    limit: int = 10


# ---- BM25 ----
class BM25SearchRequest(BaseModel):
    user_id: str
    session_id: str
    query: str
    limit: int = 10


# ---- VECTOR ----
class VectorSearchRequest(BaseModel):
    user_id: str
    session_id: str
    embedding: list[float] = Field(default_factory=_random_embedding)
    limit: int = 10


# ---- HYBRID ----
class HybridSearchRequest(BaseModel):
    user_id: str
    session_id: str
    query: str
    embedding: list[float] = Field(default_factory=_random_embedding)
    limit: int = 10
    weights: dict[str, float] = Field(default_factory=lambda: {
        "bm25": 0.4,
        "vector": 0.6
    })


# ---- RESPONSE ----
class SearchResponse(BaseModel):
    count: int
    results: list[dict]


# ---- SIMPLE RESPONSE ----
class MemoryResponse(BaseModel):
    message: str