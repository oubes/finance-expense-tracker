# ---- Imports ----
from pydantic import BaseModel, Field
from typing import Any
from langchain_core.documents import Document


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


# ---- Final Pipeline Output ----
class PipelineOutput(BaseModel):
    data: list[DocumentItem]
    meta: PipelineMeta