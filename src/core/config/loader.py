# ---- Imports ----
from src.core.config.yaml_loader import load_yaml
from src.core.config.settings import AppSettings

# ---- Settings Loader ----
def load_settings(config_path: str = "config.yaml") -> AppSettings:
    # ---- YAML Loading ----
    yaml_data = load_yaml(config_path)

    # ---- Settings Construction ----
    settings = AppSettings(**yaml_data)

    return settings