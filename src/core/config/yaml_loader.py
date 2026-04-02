from pathlib import Path
import yaml


def load_yaml(path: str) -> dict:
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(file_path, "r") as f:
        return yaml.safe_load(f) or {}