# ---- Imports ----
from pathlib import Path
from typing import Any
import logging

# ---- logging ----
logger = logging.getLogger(__name__)


# ---- Graph Saver ----
class GraphSaver:
    def __init__(self, filename: str):
        base_path = self._resolve_project_root()
        self.output_path = base_path / "data" / "graphs" / filename

    # ---- Resolve Project Root ----
    def _resolve_project_root(self) -> Path:
        current = Path.cwd().resolve()

        for parent in [current] + list(current.parents):
            if (parent / ".git").exists():
                return parent
            if (parent / "pyproject.toml").exists():
                return parent

        # fallback: assume cwd
        return current

    # ---- Save Graph ----
    def save(self, graph: Any) -> Path:
        try:
            png_bytes: bytes = graph.get_graph().draw_mermaid_png()

            self.output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.output_path, "wb") as f:
                f.write(png_bytes)

            logger.info(f"Graph saved successfully to {self.output_path}")

        except Exception as e:
            logger.exception(f"Graph save failed: {e}")
            raise

        return self.output_path