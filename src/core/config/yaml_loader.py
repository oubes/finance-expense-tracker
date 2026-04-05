# ---- Imports ----
from pathlib import Path
import yaml


# ---- YAML Loader ----
def load_yaml(path: str) -> dict:
    file_path = Path(path)

    # ---- File Existence Check ----
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    # ---- File Reading ----
    with open(file_path, "r") as f:
        return yaml.safe_load(f) or {}