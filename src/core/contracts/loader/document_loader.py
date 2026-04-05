# ---- Imports ----
from abc import ABC, abstractmethod
from langchain_core.documents import Document


# ---- Document Loader Contract ----
class DocumentLoaderContract(ABC):

    # ---- Load Documents ----
    @abstractmethod
    def load(self, file_name: str) -> list[Document]:
        pass