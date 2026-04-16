# ---- Standard Library ----
from __future__ import annotations

from collections.abc import Callable

from langchain_text_splitters import RecursiveCharacterTextSplitter
from source.ingestion_service.core.config.settings import AppSettings


class Splitter:
    # ---- Constructor ----
    def __init__(self, settings: AppSettings):
        self.chunk_size = settings.ingestion.chunk_size
        self.chunk_overlap = settings.ingestion.chunk_overlap

        # ---- Length function (pure character-based) ----
        self.length_function = len

        self._splitter = self._build_splitter()

    # ---- Build Splitter ----
    def _build_splitter(self) -> RecursiveCharacterTextSplitter:
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=self.length_function,
            is_separator_regex=False,
            separators=[
                "\n# ",
                "\n## ",
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

    # ---- Split Text ----
    def split(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        return self._splitter.split_text(text)