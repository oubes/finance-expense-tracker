# ---- Imports ----
from pathlib import Path
from typing import Any
import logging
import inspect
import re

# ---- logging ----
logger = logging.getLogger(__name__)


# ---- Graph Saver ----
class GraphSaver:
    def __init__(self, filename: str):
        base_path = self._resolve_project_root()
        parent_name = self._resolve_parent_name()

        self.output_path = base_path / "data" / "graphs" / parent_name / filename

    # ---- Resolve Project Root ----
    def _resolve_project_root(self) -> Path:
        current = Path.cwd().resolve()

        for parent in [current] + list(current.parents):
            if (parent / ".git").exists():
                return parent
            if (parent / "pyproject.toml").exists():
                return parent

        return current

    # ---- Resolve Caller Parent Name (Skip Version-like Folders) ----
    def _resolve_parent_name(self) -> str:
        try:
            caller_frame = inspect.stack()[2]
            caller_file = Path(caller_frame.filename).resolve()

            for parent in caller_file.parents:
                name = parent.name

                # skip version-like dirs: v1, v2, 1, 2, etc.
                if re.fullmatch(r"v?\d+", name, re.IGNORECASE):
                    continue

                if name:
                    return name

            return "default"

        except Exception:
            return "default"

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