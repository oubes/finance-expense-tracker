# ---- Imports ----
from abc import ABC, abstractmethod
from typing import Any
from langchain_core.documents import Document


# ---- Chunker Contract ----
class ChunkerContract(ABC):

    # ---- Chunk Documents ----
    @abstractmethod
    def chunk_documents(
        self,
        documents: list[Document],
        doc_name: str
    ) -> list[dict[str, Any]]:
        pass