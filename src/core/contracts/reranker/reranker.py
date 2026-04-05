# ---- Imports ----
from abc import ABC, abstractmethod
from typing import Any


# ---- Reranker Contract ----
class RerankerContract(ABC):

    # ---- Rerank ----
    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_k: int
    ) -> list[dict[str, Any]]:
        pass