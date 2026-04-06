# ---- Standard Library ----
import re
import unicodedata


class PostTextCleaner:
    # ---- Normalize Text ----
    def normalize_text(
        self,
        text: str,
        *,
        lowercase: bool = False,
        remove_accents: bool = False,
    ) -> str:
        text = unicodedata.normalize("NFKC", text)

        if remove_accents:
            text = self._strip_accents(text)

        if lowercase:
            text = text.lower()

        return text

    # ---- Strip Accents ----
    def _strip_accents(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text)
        return "".join(c for c in normalized if not unicodedata.combining(c))

    # ---- Normalize Whitespace ----
    def normalize_whitespace(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    # ---- Final Chunk Cleanup ----
    def clean_chunk(self, text: str) -> str:
        if not text or not text.strip():
            return ""

        text = self.normalize_whitespace(text)
        text = self.normalize_text(text)
        text = self.normalize_whitespace(text)

        return text