# ---- Imports ----
from abc import ABC, abstractmethod


# ---- Embedder Contract ----
class EmbedderContract(ABC):

    # ---- Single Text Embedding ----
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        pass

    # ---- Batch Embedding ----
    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        pass