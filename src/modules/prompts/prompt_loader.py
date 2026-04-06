# ---- Imports ----
from pathlib import Path


class PromptLoader:
    # ---- Load ----
    def load(self, file_path: str) -> dict[str, str]:
        text = Path(file_path).read_text(encoding="utf-8")

        sections: dict[str, list[str]] = {}
        current_section = None

        # ---- Parse Lines ----
        for line in text.splitlines():
            stripped = line.strip()

            if stripped.startswith("# "):
                current_section = stripped[2:].strip().lower()
                sections[current_section] = []
            else:
                if current_section:
                    sections[current_section].append(line)

        return {
            key: "\n".join(value).strip()
            for key, value in sections.items()
        }