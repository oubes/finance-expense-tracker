import logging
import re

from langchain_core.documents import Document
from src.modules.ingestion.chunker.cleaner import clean_text
from src.modules.ingestion.chunker.validator import is_valid_text
from src.modules.ingestion.chunker.metadata_enricher import enrich_metadata
from src.modules.ingestion.chunker.chunk_builder import build_chunk
from src.modules.ingestion.chunker.spiltter import Splitter
from src.core.config.loader import load_settings

logger = logging.getLogger(__name__)

settings = load_settings()


class Chunker:
    def __init__(
        self,
        base_chunk_size: int = settings.rag.chunk_size,
        chunk_overlap: int = settings.rag.chunk_overlap,
        min_length: int = 30,
    ):
        # Initialize chunking parameters and the dynamic splitting engine
        self.base_chunk_size = base_chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_length = min_length
        self.dynamic_splitter = Splitter(
            chunk_size=self.base_chunk_size, 
            chunk_overlap=self.chunk_overlap
        )

    def chunk_documents(
        self,
        documents: list[Document],
        doc_name: str,
    ) -> list[dict]:
        # Process documents into validated chunks using size-adaptive recursive splitting
        if not documents:
            logger.warning("No documents provided.")
            return []

        try:
            chunks: list[dict] = []
            chunk_counter = 0

            for doc in documents:
                cleaned_raw = clean_text(doc.page_content)

                if not is_valid_text(cleaned_raw, self.min_length):
                    continue

                meta = enrich_metadata(doc)
                splitter = self.dynamic_splitter.get_splitter(cleaned_raw)
                split_parts = splitter.split_text(cleaned_raw)

                for part in split_parts:
                    if not is_valid_text(part, self.min_length):
                        continue

                    chunk = build_chunk(
                        content=part,
                        doc_name=doc_name,
                        meta=meta,
                        chunk_index=chunk_counter,
                        raw_content=part,
                    )

                    chunks.append(chunk)
                    chunk_counter += 1

            logger.info(f"[Chunker] Generated {len(chunks)} adaptive chunks")
            return chunks

        except Exception:
            logger.exception("chunk_documents failed")
            raise