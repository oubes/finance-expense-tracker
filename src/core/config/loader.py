from src.core.config.yaml_loader import load_yaml
from src.core.config.settings import AppSettings

def load_settings(config_path: str = "config.yaml") -> AppSettings:
    yaml_data = load_yaml(config_path)

    settings = AppSettings(**yaml_data)

    return settings