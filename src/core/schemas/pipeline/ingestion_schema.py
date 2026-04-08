# ---- Imports ----
from pydantic import BaseModel, Field
from typing import Any
from uuid import UUID
from datetime import datetime


# ---- Summary Schema ----
class SummaryModel(BaseModel):
    title: str
    summary: str
    flag: str = Field(pattern="^SUCCESS_FLAG$")


# ---- Content Schema ----
class ContentModel(BaseModel):
    title: str
    text: str
    summary: SummaryModel


# ---- Document Schema ----
class DocumentModel(BaseModel):
    title: str


# ---- Final Document Item ----
class DocumentItem(BaseModel):
    document: DocumentModel
    content: ContentModel
    vector: list[float]
    metadata: dict[str, Any]


# ---- Pipeline Metadata ----
class PipelineMeta(BaseModel):
    pipeline_version: str
    count: int


# ---- Nested Metadata ----
class ChunkMetadata(BaseModel):
    page_label: str | None = None


# ---- Main DB Record ----
class PipelineOutput(BaseModel):
    # ---- IDs ----
    id: UUID
    chunk_id: UUID

    # ---- Core Retrieval ----
    content: str
    summary: str

    # ---- Semantic Labels ----
    chunk_title: str

    # ---- Document Context ----
    doc_title: str
    source: str
    score: float = Field(ge=0.0, le=1.0)

    # ---- Position ----
    page: int | None = None
    total_pages: int | None = None

    # ---- System ----
    created_at: datetime
    
    # ---- Pipeline Metadata ----
    pipeline_version: str
    
    # ---- Embedding ----
    embedding: list[float]