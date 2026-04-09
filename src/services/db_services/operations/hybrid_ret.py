# ---- Imports ----
import logging
from typing import Any

from src.core.contracts.retrieval.retriever import RetrieverContract

logger = logging.getLogger(__name__)


# ---- Hybrid Retriever ----
class HybridRetriever(RetrieverContract):

    # ---- Constructor ----
    def __init__(
        self,
        bm25_retriever: RetrieverContract,
        vector_retriever: RetrieverContract,
        reranker: Any,
    ):
        self.bm25_retriever = bm25_retriever
        self.vector_retriever = vector_retriever
        self.reranker = reranker

    # ---- Search ----
    async def search(self, input_query: str, limit: int = 10) -> list[dict[str, Any]]:
        logger.info("stage=hybrid_retrieval_start")

        try:
            # ---- Input Validation ----
            if not input_query or not isinstance(input_query, str):
                raise ValueError("Invalid input_query provided")

            if limit <= 0:
                raise ValueError("Limit must be greater than 0")

            # ---- Retrieval ----
            bm25_results = await self.bm25_retriever.search(input_query, limit)
            vector_results = await self.vector_retriever.search(input_query, limit)

            # ---- Merge ----
            merged = self._merge(bm25_results, vector_results)

            # ---- Rerank ----
            ranked = self.reranker.rerank(merged)

            logger.info("stage=hybrid_retrieval_completed")

            return ranked

        except Exception:
            logger.exception("stage=hybrid_retrieval_failed")
            return []

    # ---- Merge ----
    def _merge(
        self,
        bm25_results: list[dict[str, Any]],
        vector_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        index: dict[str, dict[str, Any]] = {}

        try:
            for r in (bm25_results or []) + (vector_results or []):
                if not isinstance(r, dict):
                    continue

                doc_id = r.get("id")
                if not doc_id:
                    continue

                if doc_id not in index:
                    index[doc_id] = dict(r)
                else:
                    index[doc_id].update(r)

            return list(index.values())

        except Exception:
            logger.exception("stage=merge_failed")
            return []