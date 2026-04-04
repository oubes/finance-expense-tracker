import logging
from typing import Any

from src.modules.retrieval.bm25_retrieval import BM25Retriever
from src.modules.retrieval.vector_retriever import VectorRetriever

logger = logging.getLogger(__name__)

# Combines BM25 and vector retrieval results
class HybridRetriever:
    def __init__(self, bm25: BM25Retriever, vector: VectorRetriever):
        self.bm25 = bm25
        self.vector = vector

    # Main hybrid search pipeline
    async def search(
        self,
        query: str,
        limit: int = 10,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
    ) -> list[dict[str, Any]]:
        logger.info("Hybrid search started")

        bm25_res, vec_res = await self._fetch(query, limit)
        bm25_res = self._normalize(bm25_res, "score")
        vec_res = self._normalize_and_invert(vec_res, "distance")

        combined = self._merge(bm25_res, vec_res, bm25_weight, vector_weight)
        final = self._rank(combined, limit)

        logger.info(f"Hybrid search returned {len(final)} results")
        return final

    # Fetch both retrievers results
    async def _fetch(self, query: str, limit: int):
        return (
            await self.bm25.search(query, limit * 2),
            await self.vector.search(query, limit * 2),
        )

    # Normalize scores to 0..1
    def _normalize(self, results: list, key: str) -> list:
        if not results:
            return []
        values = [r[key] for r in results]
        max_s, min_s = max(values), min(values)

        for r in results:
            r["norm_score"] = 1.0 if max_s == min_s else (r[key] - min_s) / (max_s - min_s)

        return results

    # Normalize and invert distance scores
    def _normalize_and_invert(self, results: list, key: str) -> list:
        results = self._normalize(results, key)
        for r in results:
            r["norm_score"] = 1 - r["norm_score"]
        return results

    # Merge bm25 and vector results
    def _merge(
        self,
        bm25_results: list,
        vector_results: list,
        bm25_weight: float,
        vector_weight: float,
    ) -> dict[str, dict[str, Any]]:
        combined: dict[str, dict[str, Any]] = {}

        for r in bm25_results:
            combined[r["id"]] = {
                "id": r["id"],
                "content": r["content"],
                "score": bm25_weight * r["norm_score"],
            }

        for r in vector_results:
            if r["id"] in combined:
                combined[r["id"]]["score"] += vector_weight * r["norm_score"]
            else:
                combined[r["id"]] = {
                    "id": r["id"],
                    "content": r["content"],
                    "score": vector_weight * r["norm_score"],
                }

        return combined

    # Sort and apply limit
    def _rank(self, combined: dict, limit: int) -> list[dict[str, Any]]:
        return sorted(combined.values(), key=lambda x: x["score"], reverse=True)[:limit]