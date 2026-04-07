# ---- Imports ----
from pathlib import Path
from typing import Any, Optional
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
        """Resolve project root by looking for markers like .git or pyproject.toml"""
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
        """Render and persist graph as PNG"""
        png_bytes: bytes = graph.get_graph().draw_mermaid_png()

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_path, "wb") as f:
            f.write(png_bytes)

        logger.info(f"Graph saved to {self.output_path}")
        return self.output_path