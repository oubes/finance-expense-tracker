# ---- Imports ----
from abc import ABC, abstractmethod
from typing import Any


# ---- Retriever Contract ----
class RetrieverContract(ABC):

    # ---- Search ----
    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        pass