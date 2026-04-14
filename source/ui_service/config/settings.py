from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(frozen=True)

    APP_NAME: str = "UI Service"
    VERSION: str = "0.1.0"