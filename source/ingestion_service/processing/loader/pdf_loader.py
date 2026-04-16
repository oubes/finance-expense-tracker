# ---- Imports ----
import logging
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, PyMuPDFLoader
from langchain_core.documents import Document
from source.ingestion_service.core.config.settings import AppSettings


logger = logging.getLogger(__name__)


# ---- PyPDF Loader ----
class PyPDFDocumentLoader:
    # ---- Constructor ----
    def __init__(self, settings: AppSettings):
        self.data_dir = Path(settings.ingestion_data.raw_data_dir)

    # ---- Load Method ----
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


# ---- PyMuPDF Loader ----
class PyMuPDFDocumentLoader:
    # ---- Constructor ----
    def __init__(self, settings: AppSettings):
        self.data_dir = Path(settings.ingestion_data.raw_data_dir)

    # ---- Load Method ----
    def load(self, file_name: str) -> list[Document]:
        try:
            file_path = self.data_dir / file_name

            if not file_path.exists():
                raise FileNotFoundError(f"{file_path} not found")

            loader = PyMuPDFLoader(str(file_path))
            documents = loader.load()

            logger.info(f"Loaded {len(documents)} pages from {file_name}")

            return documents

        except Exception:
            logger.exception("load_pymupdf failed")
            raise