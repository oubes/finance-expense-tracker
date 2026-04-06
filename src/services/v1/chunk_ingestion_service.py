# ---- Imports ----
import logging
from typing import Any

from pydantic import ValidationError

from src.pipelines.v1.schemas.ingestion_schema import PipelineOutput


# ---- Service ----
class ChunkIngestionService:
    def __init__(self, db: Any, collection: str) -> None:
        self._db = db
        self._collection = collection
        self._logger = logging.getLogger(__name__)

    # ---- Entry ----
    def ingest(self, payload: dict) -> None:
        parsed = self._validate(payload)
        if not parsed:
            return

        records = self._transform(parsed)
        # self._insert(records)

    # ---- Validation (Schema-level) ----
    def _validate(self, payload: dict) -> PipelineOutput | None:
        try:
            return PipelineOutput.model_validate(payload)
        except ValidationError as e:
            self._logger.error(f"Schema validation failed: {e}")
            return None

    # ---- Transform ----
    def _transform(self, data: PipelineOutput) -> list[dict]:
        return [
            {
                "id": self._build_id(item),
                "vector": item.vector,
                "text": item.content.text,
                "title": item.content.title,
                "summary": item.content.summary.summary,
                "doc_title": item.document.title,
                "metadata": item.metadata | {
                    "pipeline_version": data.meta.pipeline_version
                }
            }
            for item in data.data
        ]

    # ---- ID Builder ----
    def _build_id(self, item) -> str:
        return f"{item.document.title}:{item.content.title}"

    # ---- Insert ----
    def _insert(self, records: list[dict]) -> None:
        if not records:
            return

        self._db.insert_many(self._collection, records)
        
        
ChunkIngestionService(db=None, collection="chunks")