# ---- Imports ----
from abc import ABC, abstractmethod


# ---- Cross Encoder Contract ----
class CrossEncoderContract(ABC):

    # ---- Single Pair Scoring ----
    @abstractmethod
    def score_pair(self, query: str, document: str) -> float:
        pass

    # ---- Batch Pair Scoring ----
    @abstractmethod
    def score_pairs(self, pairs: list[tuple[str, str]]) -> list[float]:
        pass

    # ---- Document Scoring ----
    @abstractmethod
    def score_documents(self, query: str, documents: list[str]) -> list[float]:
        pass