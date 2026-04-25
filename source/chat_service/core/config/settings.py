from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="source/chat_service/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # ------------------ application ------------------
    APP_NAME: str = "chat-service"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # ------------------ server ------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # ------------------ services ------------------
    INFRA_SERVICE_URL: str = Field(default="http://localhost:8003")

    # ------------------ resilience: circuit breaker ------------------
    CB_FAIL_THRESHOLD: int = 3
    CB_RESET_TIMEOUT: int = 10

    # ------------------ resilience: retry ------------------
    RETRY_ATTEMPTS: int = 5
    RETRY_BACKOFF: float = 0.5

    # ------------------ http client ------------------
    HTTP_TIMEOUT_SECONDS: float = 2.0
    HTTP_CONNECT_TIMEOUT: float = 2.0
    HTTP_READ_TIMEOUT: float = 5.0
    HTTP_WRITE_TIMEOUT: float = 5.0
    HTTP_POOL_TIMEOUT: float = 2.0

    HTTP_MAX_CONNECTIONS: int = 100
    HTTP_MAX_KEEPALIVE_CONNECTIONS: int = 20
    