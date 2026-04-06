# ---- Imports ----
from pathlib import Path
from src.core.config.settings import AppSettings


class PromptRegistry:
    # ---- Constructor ----
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.base_dir = Path(self.settings.ingestion.prompt_templates_dir)
        self._registry: dict[str, Path] = {}

        self._load_prompts()

    # ---- Scan Directory ----
    def _load_prompts(self) -> None:
        for file_path in self.base_dir.glob("*.md"):
            key = file_path.stem
            self._registry[key] = file_path

    # ---- Resolve Prompt Path ----
    def get(self, name: str) -> str:
        if name not in self._registry:
            raise ValueError(f"Prompt not found: {name}")

        return str(self._registry[name])

    # ---- List Available ----
    def list(self) -> list[str]:
        return list(self._registry.keys())