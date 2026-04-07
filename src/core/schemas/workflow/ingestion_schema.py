# ---- Imports ----
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class WorkflowOutput(BaseModel):
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

    # ---- Position ----
    page: int | None = None
    total_pages: int | None = None

    # ---- System ----
    created_at: datetime
    
    # ---- Pipeline Metadata ----
    pipeline_version: str
    
    # ---- Embedding ----
    embedding: list[float]
    