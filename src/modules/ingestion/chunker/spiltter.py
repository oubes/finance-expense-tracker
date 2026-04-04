from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.core.config.settings import AppSettings


class Splitter:
    def __init__(self, settings: AppSettings):
        self.chunk_size = settings.rag.chunk_size
        self.chunk_overlap = settings.rag.chunk_overlap
        self._splitter = self._build_splitter()

    # ---- Build Splitter ----
    def _build_splitter(self) -> RecursiveCharacterTextSplitter:
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n", "\n", " ", ""],
        )

    # ---- Split Text ----
    def split(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        return self._splitter.split_text(text)