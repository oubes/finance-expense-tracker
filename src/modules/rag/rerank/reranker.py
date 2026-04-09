# ---- Imports ----
import logging
from typing import Any

logger = logging.getLogger(__name__)


# ---- Reranker ----
class Reranker:

    # ---- Constructor ----
    def __init__(
        self,
        bm25_weight: float = 0.4,
        vector_weight: float = 0.4,
        stored_weight: float = 0.2,
    ):
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.stored_weight = stored_weight

        # ---- Weights Validation ----
        total_weight = self.bm25_weight + self.vector_weight + self.stored_weight
        if total_weight <= 0:
            raise ValueError("Weights must sum to a positive value")

    # ---- Rerank ----
    def rerank(self, docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        logger.info("stage=rerank_start")

        try:
            if not isinstance(docs, list):
                raise ValueError("docs must be a list")

            if len(docs) == 0:
                logger.info("stage=rerank_empty_input")
                return []

            for d in docs:
                if not isinstance(d, dict):
                    raise ValueError("Each document must be a dict")

                bm25_score = float(d.get("bm25_score", 0.0))
                vector_score = float(d.get("vector_score", 0.0))
                stored_score = float(d.get("score", 0.0))

                # ---- Score Computation ----
                total_score = (
                    self.bm25_weight * bm25_score
                    + self.vector_weight * vector_score
                    + self.stored_weight * stored_score
                )

                d["total_score"] = total_score

            # ---- Sorting ----
            ranked = sorted(docs, key=lambda x: x.get("total_score", 0.0), reverse=True)

            logger.info("stage=rerank_completed")

            return ranked

        except Exception:
            logger.exception("stage=rerank_failed")
            return []