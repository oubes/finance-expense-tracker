# ---- Imports ----
import logging
from typing import Any

logger = logging.getLogger(__name__)


# ---- Reranker ----
class Reranker:

    # ---- Constructor ----
    def __init__(self):
        pass

    # ---- Normalize Scores Vector ----
    def _normalize_vector(self, scores: dict[str, float]) -> dict[str, float]:
        total = sum(scores.values())

        if total <= 0:
            return {k: 0.0 for k in scores}

        # ---- If already normalized ----
        if abs(total - 1.0) < 1e-6:
            return scores

        # ---- Scale to sum = 1 ----
        return {k: v / total for k, v in scores.items()}

    # ---- Rerank ----
    def rerank(
        self,
        docs: list[dict[str, Any]],
        *,
        bm25_weight: float,
        vector_weight: float,
        stored_weight: float,
    ) -> list[dict[str, Any]]:
        logger.info("stage=rerank_start")

        try:
            if not isinstance(docs, list):
                raise ValueError("docs must be a list")

            if len(docs) == 0:
                return []

            weights = {
                "bm25": float(bm25_weight),
                "vector": float(vector_weight),
                "stored": float(stored_weight),
            }

            weights = self._normalize_vector(weights)

            for d in docs:
                if not isinstance(d, dict):
                    raise ValueError("Each document must be a dict")

                bm25_score = float(d.get("bm25_score", 0.0))
                vector_score = float(d.get("vector_score", 0.0))
                stored_score = float(d.get("score", 0.0))

                # ---- Final Score ----
                total_score = (
                    weights["bm25"] * bm25_score
                    + weights["vector"] * vector_score
                    + weights["stored"] * stored_score
                )

                d["total_score"] = total_score

            ranked = sorted(docs, key=lambda x: x.get("total_score", 0.0), reverse=True)

            logger.info("stage=rerank_completed")

            return ranked

        except Exception:
            logger.exception("stage=rerank_failed")
            return []