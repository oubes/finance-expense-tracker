from pydantic import BaseModel, Field


# ---- Single Embedding ----
class EmbedRequest(BaseModel):
    text: str = Field(..., min_length=1)


class EmbedResponse(BaseModel):
    embedding: list[float]


# ---- Batch Embedding ----
class BatchEmbedRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1)


class BatchEmbedItem(BaseModel):
    text: str
    embedding: list[float]


class BatchEmbedResponse(BaseModel):
    results: list[BatchEmbedItem]
    count: int