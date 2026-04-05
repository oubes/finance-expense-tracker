# ---- Standard Library ----
import logging
from typing import Any

# ---- External ----
from langchain_core.documents import Document

# ---- Internal ----
from src.core.contracts.chunking.chunker import ChunkerContract
from src.modules.ingestion.chunker.cleaner import TextCleaner
from src.modules.ingestion.chunker.validator import TextValidator
from src.modules.ingestion.chunker.toc_classifier import TOCClassifier
from src.modules.ingestion.chunker.spiltter import Splitter
from src.modules.ingestion.chunker.scoring import ChunkScorer

logger = logging.getLogger(__name__)


class Chunker(ChunkerContract):
    # ---- Initialization ----
    def __init__(
        self,
        config: Any,
        cleaner: TextCleaner,
        validator: TextValidator,
        toc_classifier: TOCClassifier,
        splitter: Splitter,
        scorer: ChunkScorer,
    ):
        self.cleaner = cleaner
        self.validator = validator
        self.toc_classifier = toc_classifier
        self.scorer = scorer

        self.base_chunk_size = config.rag.chunk_size
        self.chunk_overlap = config.rag.chunk_overlap
        self.min_length = getattr(config, "min_length", 30)

        self.splitter = splitter

    # ---- Public API ----
    def chunk_documents(self, documents: list[Document], doc_name: str) -> list[dict]:
        if not documents:
            logger.warning("No documents provided.")
            return []

        chunks: list[dict] = []
        chunk_counter = 0

        for doc in documents:
            try:
                cleaned_raw = self._clean_text(doc.page_content)

                if not self._is_valid_text(cleaned_raw):
                    continue

                meta = self._enrich_metadata(doc)

                split_parts = self._split_text(cleaned_raw)
                if not split_parts:
                    continue

                for part in split_parts:
                    if not self._is_valid_text(part):
                        continue

                    score = self._compute_score(part, cleaned_raw)

                    chunk = self._build_chunk(
                        content=part,
                        doc_name=doc_name,
                        meta=meta,
                        chunk_index=chunk_counter,
                        raw_content=part,
                        score=score,
                    )

                    chunks.append(chunk)
                    chunk_counter += 1

            except Exception:
                logger.exception("Failed processing document")
                continue

        logger.info(f"[Chunker] Generated {len(chunks)} adaptive chunks")
        return chunks

    # ---- Text Cleaning ----
    def _clean_text(self, text: str) -> str:
        try:
            return self.cleaner.clean_text(text)
        except Exception:
            logger.exception("Text cleaning failed")
            return ""

    # ---- Validation ----
    def _is_valid_text(self, text: str) -> bool:
        try:
            return self.validator.is_valid_text(text, self.min_length)
        except Exception:
            logger.exception("Text validation failed")
            return False

    # ---- Metadata Enrichment ----
    def _enrich_metadata(self, doc: Document) -> dict:
        try:
            return self.toc_classifier.enrich_metadata(doc)
        except Exception:
            logger.exception("Metadata enrichment failed")
            return doc.metadata.copy()

    # ---- Splitting ----
    def _split_text(self, text: str) -> list[str]:
        try:
            return self.splitter.split(text)
        except Exception:
            logger.exception("Text splitting failed")
            return []

    # ---- Scoring ----
    def _compute_score(self, text: str, raw_text: str) -> float:
        try:
            return self.scorer.score(text, raw_text)
        except Exception:
            logger.exception("Scoring failed")
            return 0.0

    # ---- Chunk Builder ----
    def _build_chunk(self, content: str, doc_name: str, meta: dict, chunk_index: int, raw_content: str, score: float) -> dict:
        return {
            "content": content,
            "doc_name": doc_name,
            "metadata": meta,
            "chunk_index": chunk_index,
            "raw_content": raw_content,
            "score": score,
        }