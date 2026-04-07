# ---- Imports ----
from pathlib import Path
from typing import Any


# ---- Graph Saver ----
class GraphSaver:
    def __init__(self, filename: str):
        base_path = Path.cwd().parent / "data" / "graphs"
        self.output_path = base_path / filename

    def save(self, graph: Any) -> Path:
        png_bytes: bytes = graph.get_graph().draw_mermaid_png()

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_path, "wb") as f:
            f.write(png_bytes)

        print(f"Graph saved to {self.output_path}")
        return self.output_path