import logging
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from src.core.contracts.loader.document_loader import DocumentLoaderContract

logger = logging.getLogger(__name__)


class PDFDocumentLoader(DocumentLoaderContract):
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)

    def load(self, file_name: str) -> list[Document]:
        try:
            file_path = self.data_dir / file_name

            if not file_path.exists():
                raise FileNotFoundError(f"{file_path} not found")

            loader = PyPDFLoader(str(file_path))
            documents = loader.load()

            logger.info(f"Loaded {len(documents)} pages from {file_name}")

            return documents

        except Exception:
            logger.exception("load_pdf failed")
            raise