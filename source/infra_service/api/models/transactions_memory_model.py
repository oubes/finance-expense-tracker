# ---- Imports ----
from pydantic import BaseModel, Field
import numpy as np


# ---- Embedding (test only) ----
def _random_embedding(dim: int = 1024):
    return np.round(np.random.rand(dim), 4).tolist()


# ---- BASE ----
class TransactionBase(BaseModel):
    user_id: str
    session_id: str

    product: str | None = None
    category: str | None = None

    amount: float | None = None
    quantity: float | None = None
    currency: str | None = None

    note: str | None = None
    raw_input: str


# ---- ADD EVENT ----
class AddTransactionRequest(TransactionBase):
    embedding: list[float] = Field(default_factory=_random_embedding)


# ---- HISTORY ----
class UserTransactionsRequest(BaseModel):
    user_id: str
    session_id: str


# ---- CATEGORY ----
class CategoryTransactionsRequest(BaseModel):
    user_id: str
    session_id: str
    category: str


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


class MemoryResponse(BaseModel):
    message: str