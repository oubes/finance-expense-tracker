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
        reranker,
    ):
        self.bm25_retriever = bm25_retriever
        self.vector_retriever = vector_retriever
        self.reranker = reranker

    # ---- Search ----
    async def search(self, input_query: str, limit: int = 5, weights: dict[str, float]={"bm25":0.15, "vector":0.8, "stored":0.05}) -> list[dict[str, Any]]:
        logger.info("stage=hybrid_retrieval_start query_length=%s limit=%s", len(input_query or ""), limit)

        if not input_query or not isinstance(input_query, str):
            raise ValueError("Invalid input_query")

        if limit <= 0:
            raise ValueError("Limit must be > 0")

        bm25_raw, vector_raw = await self._fetch(input_query, limit)

        bm25 = self._normalize_rows(bm25_raw)
        vector = self._normalize_rows(vector_raw)

        bm25 = self._attach_bm25_score(bm25)
        vector = self._attach_vector_scores(vector)

        merged = self._merge(bm25, vector)
        results = list(merged.values())

        # ---- Rerank (Single Source of Truth) ----
        if self.reranker:
            results = self.reranker.rerank(
                results,
                bm25_weight=weights.get("bm25", 0.15),
                vector_weight=weights.get("vector", 0.8),
                stored_weight=weights.get("stored", 0.05),
            )

        else:
            raise RuntimeError("Reranker is required but not provided")

        return results[:limit]

    # ---- Fetch ----
    async def _fetch(self, query: str, limit: int):
        bm25_task = self.bm25_retriever.search(query, limit * 2)
        vector_task = self.vector_retriever.search(query, limit * 2)

        bm25_results, vector_results = await bm25_task, await vector_task

        return bm25_results, vector_results

    # ---- Normalize Rows ----
    def _normalize_rows(self, results: list[Any]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []

        for r in results or []:
            if isinstance(r, dict):
                normalized.append(r)
            else:
                normalized.append(self._tuple_to_dict(r))

        return normalized

    # ---- Tuple Mapping ----
    def _tuple_to_dict(self, row: Any) -> dict[str, Any]:
        return {
            "id": row[0],
            "content": row[1],
            "summary": row[2],
            "chunk_title": row[3],
            "doc_title": row[4],
            "bm25_score": float(row[5]) if row[5] is not None else 0.0,
            "vector_score": float(row[6]) if len(row) > 6 and row[6] is not None else 0.0,
        }

    # ---- Attach BM25 Score ----
    def _attach_bm25_score(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for r in results:
            r["bm25_score"] = float(r.get("bm25_score", 0.0))
        return results

    # ---- Attach Vector Score ----
    def _attach_vector_scores(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for r in results:
            r["vector_score"] = float(r.get("vector_score", 0.0))
        return results

    # ---- Merge ----
    def _merge(
        self,
        bm25_results: list[dict[str, Any]],
        vector_results: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:

        index: dict[str, dict[str, Any]] = {}

        for r in bm25_results:
            doc_id = r.get("id")
            if not doc_id:
                continue

            index[doc_id] = {
                "id": doc_id,
                "content": r.get("content"),
                "summary": r.get("summary"),
                "bm25_score": r.get("bm25_score", 0.0),
                "vector_score": 0.0,
                "chunk_score": 0.0,
            }

        for r in vector_results:
            doc_id = r.get("id")
            if not doc_id:
                continue

            vec_score = r.get("vector_score", 0.0)

            if doc_id in index:
                index[doc_id]["vector_score"] = vec_score
            else:
                index[doc_id] = {
                    "id": doc_id,
                    "content": r.get("content"),
                    "summary": r.get("summary"),
                    "bm25_score": 0.0,
                    "vector_score": vec_score,
                    "chunk_score": 0.0,
                }

        return index