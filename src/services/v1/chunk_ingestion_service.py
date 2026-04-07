# ---- Imports ----
import logging
from typing import Any

from pydantic import ValidationError
from src.core.schemas.pipeline.ingestion_schema import PipelineOutput

logger = logging.getLogger(__name__)

# ---- Service ----
class ChunkIngestionService:
    def __init__(
        self,
        client: Any,
        collection: str,
        batch_size: int = 128
    ) -> None:
        self._client = client
        self._collection = collection
        self._batch_size = batch_size

    # ---- Entry ----
    async def ingest(self, payload: dict) -> None:
        parsed = self._validate(payload)
        if not parsed:
            return

        records = self._transform(parsed)
        await self._insert(records)

    # ---- Validation ----
    def _validate(self, payload: dict) -> PipelineOutput | None:
        try:
            return PipelineOutput.model_validate(payload)
        except ValidationError as e:
            logger.error(f"Schema validation failed: {e}")
            return None

    # ---- Transform ----
    def _transform(self, data: PipelineOutput) -> list[dict]:
        records: list[dict] = []

        for item in data.data:
            record = {
                "id": self._build_id(item),
                "vector": item.vector,
                "text": item.content.text,
                "metadata": {
                    **item.metadata,
                    "doc_title": item.document.title,
                    "content_title": item.content.title,
                    "summary": item.content.summary.summary,
                    "pipeline_version": data.meta.pipeline_version,
                },
            }
            records.append(record)

        return records

    # ---- ID Builder ----
    def _build_id(self, item: Any) -> str:
        return f"{item.document.title}:{item.content.title}"

    # ---- Insert (Batched) ----
    async def _insert(self, records: list[dict]) -> None:
        if not records:
            logger.warning("No valid records to insert")
            return

        total = len(records)

        for i in range(0, total, self._batch_size):
            batch = records[i : i + self._batch_size]

            try:
                await self._client.insert_many(
                    collection=self._collection,
                    records=batch,
                )
            except Exception as e:
                logger.error(f"Batch insert failed: {e}")