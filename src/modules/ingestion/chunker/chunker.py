import logging
from src.modules.ingestion.chunker.cleaner import clean_text
from src.modules.ingestion.chunker.validator import is_valid_text
from src.modules.ingestion.chunker.spiltter import DynamicSplitter
from src.modules.ingestion.chunker.metadata_enricher import enrich_metadata
from src.modules.ingestion.chunker.chunk_builder import build_chunk

logger = logging.getLogger(__name__)


class Chunker:
    def __init__(
        self,
        base_chunk_size: int,
        chunk_overlap: int,
        min_length: int = 30,
    ):
        self.base_chunk_size = base_chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_length = min_length

        self.splitter = DynamicSplitter(base_chunk_size, chunk_overlap)

    def chunk_documents(
        self,
        documents: list[Document],
        doc_name: str,
    ) -> list[dict]:

        if not documents:
            logger.warning("No documents provided.")
            return []

        try:
            chunks: list[dict] = []
            chunk_counter = 0

            for doc in documents:
                raw_text = doc.page_content
                cleaned = clean_text(raw_text)

                if not is_valid_text(cleaned, self.min_length):
                    continue

                splitter = self.splitter.get_splitter(cleaned)
                split_parts = splitter.split_text(cleaned)

                meta = enrich_metadata(doc)

                for part in split_parts:
                    part_clean = clean_text(part)

                    if not is_valid_text(part_clean, self.min_length):
                        continue

                    chunk = build_chunk(
                        content=part_clean,
                        doc_name=doc_name,
                        meta=meta,
                        chunk_index=chunk_counter,
                    )

                    chunks.append(chunk)
                    chunk_counter += 1

            logger.info(f"[Chunker] Generated {len(chunks)} chunks")
            return chunks

        except Exception:
            logger.exception("chunk_documents failed")
            raise
