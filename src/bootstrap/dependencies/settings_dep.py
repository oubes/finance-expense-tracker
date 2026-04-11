# ---- Standard Library ----
import logging
from functools import lru_cache

# ---- Core Config ----
from src.core.config.loader import load_settings
from src.core.config.settings import AppSettings

logger = logging.getLogger(__name__)


# ---- Settings Provider ----
@lru_cache()
def get_settings() -> AppSettings:
    logger.info("Loading application settings")
    return load_settings()