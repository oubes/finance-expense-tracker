from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # ------------------ pydantic config ------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------ application ------------------
    APP_NAME: str = "api-gateway"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # ------------------ server ------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ------------------ services ------------------
    CHAT_SERVICE_URL: str = "http://rag:8001"
    INGESTION_SERVICE_URL: str = "http://ingestion:8002"

    # ------------------ resilience: circuit breaker ------------------
    CB_FAIL_THRESHOLD: int = 3
    CB_RESET_TIMEOUT: int = 10

    # ------------------ resilience: retry ------------------
    RETRY_ATTEMPTS: int = 5
    RETRY_BACKOFF: float = 0.5

    # ------------------ http client ------------------
    HTTP_CONNECT_TIMEOUT: float = 2.0
    HTTP_READ_TIMEOUT: float = 5.0
    HTTP_WRITE_TIMEOUT: float = 5.0
    HTTP_POOL_TIMEOUT: float = 2.0

    HTTP_MAX_CONNECTIONS: int = 100
    HTTP_MAX_KEEPALIVE_CONNECTIONS: int = 20