import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Settings Schema (ENV-driven) ----
class Settings(BaseSettings):

    # ---- Pydantic Config ----
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # ---- Application ----
    APP_NAME: str = "api-gateway"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # ---- Server ----
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ---- External Services URLs ----
    CHAT_SERVICE_URL: str = "http://rag:8001"
    INGESTION_SERVICE_URL: str = "http://ingestion:8002"

    # ---- HTTP Config ----
    HTTP_TIMEOUT_SECONDS: int = 10

    # ---- Lifecycle Hooks ----
    def __init__(self, **values):
        logger.info("[SETTINGS] initializing settings object")

        try:
            super().__init__(**values)
            logger.info(
                "[SETTINGS] loaded successfully | env=%s debug=%s log_level=%s",
                self.APP_ENV,
                self.DEBUG,
                self.LOG_LEVEL
            )

        except Exception:
            logger.exception("[SETTINGS] failed to load settings")
            raise