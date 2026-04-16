# ---- Standard Library ----
import logging
from typing import Any

# ---- External ----
from langchain_core.documents import Document

# ---- Internal ----
from source.ingestion_service.processing.chunker.cleaner_pre import PreTextCleaner
from source.ingestion_service.processing.chunker.cleaner_post import PostTextCleaner
from source.ingestion_service.processing.chunker.validator import TextValidator
from source.ingestion_service.processing.chunker.toc_classifier import TOCClassifier
from source.ingestion_service.processing.chunker.spiltter import Splitter
from source.ingestion_service.processing.chunker.scoring import ChunkScorer

logger = logging.getLogger(__name__)


class Chunker:
    # ---- Initialization ----
    def __init__(
        self,
        config: Any,
        pre_cleaner: PreTextCleaner,
        post_cleaner: PostTextCleaner,
        validator: TextValidator,
        toc_classifier: TOCClassifier,
        splitter: Splitter,
        scorer: ChunkScorer,
    ):
        self.pre_cleaner = pre_cleaner
        self.post_cleaner = post_cleaner
        self.validator = validator
        self.toc_classifier = toc_classifier
        self.splitter = splitter
        self.scorer = scorer

        self.min_length = getattr(config, "min_length", 30)

    # ---- Public API ----
    def chunk_documents(self, documents: list[Document], doc_name: str) -> list[dict]:
        if not documents:
            logger.warning("No documents provided.")
            return []

        # ---- Normalize nested input ----
        if documents and isinstance(documents[0], list):
            documents = [
                doc
                for sublist in documents
                for doc in sublist
                if isinstance(doc, Document)
            ]

        chunks: list[dict] = []
        chunk_counter = 0

        for doc in documents:
            try:
                # ---- Type Safety ----
                if not isinstance(doc, Document):
                    logger.warning(f"Skipping invalid document type: {type(doc)}")
                    continue

                raw_text = doc.page_content

                # ---- Pre-Cleaning ----
                cleaned_text = self.pre_cleaner.clean(raw_text)

                # ---- Pre-Validation ----
                if not self.validator.is_valid_text(cleaned_text, self.min_length):
                    continue

                # ---- Metadata / Classification ----
                meta = self.toc_classifier.enrich_metadata(doc)

                # ---- Splitting ----
                parts = self.splitter.split(cleaned_text)
                if not parts:
                    continue

                for part in parts:
                    # ---- Post-Cleaning ----
                    final_part = self.post_cleaner.clean_chunk(part)

                    if not final_part:
                        continue

                    # ---- Post-Validation ----
                    if not self.validator.is_valid_text(final_part, self.min_length):
                        continue

                    # ---- Scoring ----
                    score = self.scorer.score(final_part, cleaned_text)

                    # ---- Chunk Build ----
                    chunks.append(
                        {
                            "content": final_part,
                            "doc_name": doc_name,
                            "metadata": meta,
                            "chunk_index": chunk_counter,
                            "raw_content": part,
                            "score": score,
                        }
                    )

                    chunk_counter += 1

            except Exception:
                logger.exception("Failed processing document")
                continue

        logger.info(f"[Chunker] Generated {len(chunks)} adaptive chunks")
        return chunks