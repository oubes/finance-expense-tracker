from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        frozen=True
    )

    APP_NAME: str = "UI Service"
    VERSION: str = "0.1.0"
    API_GATEWAY_URL: str = "http://localhost:8000"

settings = Settings()