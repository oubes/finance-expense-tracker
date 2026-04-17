from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


# ------------------ LLM CONFIG ------------------
class LLMConfig(BaseSettings):
    provider: str
    base_url: str
    model: str
    temperature: float = Field(0.1, ge=0.0, le=1.0)
    max_tokens: int = Field(256, gt=0)
    max_retries: int = Field(3, gt=0)
    base_delay: float = Field(0.5, gt=0.0)
    max_context_tokens: int = Field(4096, gt=0)


# ------------------ EMBEDDINGS ------------------
class EmbeddingsConfig(BaseSettings):
    model: str
    dimension: int = Field(1024, gt=0)
    max_concurrency: int = Field(5, gt=0)
    max_retries: int = Field(3, gt=0)
    base_delay: float = Field(0.5, gt=0.0)

# ------------------ DB POOL ------------------
class DBPoolConfig(BaseSettings):
    min_size: int = Field(10, gt=0)
    max_size: int = Field(25, gt=0)
    timeout: int = Field(30, gt=0)
    max_idle: int = Field(300, gt=0)
    max_lifetime: int = Field(3600, gt=0)


# ------------------ VECTOR DB ------------------
class VectorDBConfig(BaseSettings):
    enabled: bool
    table: str


# ------------------ APP SETTINGS ------------------
class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="source/infra_service/.env",
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
    PORT: int = 8003

    # ------------------ external APIs ------------------
    ALIBABA_API_KEY: str | None = Field(default=None, alias="ALIBABA_API_KEY")

    # ------------------ postgres env ------------------
    POSTGRES_HOST: str = Field(alias="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(alias="POSTGRES_PORT")
    POSTGRES_DB: str = Field(alias="POSTGRES_DB")
    POSTGRES_USER: str = Field(alias="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(alias="POSTGRES_PASSWORD")
    POSTGRES_DB_TYPE: str = Field(alias="POSTGRES_DB_TYPE")

    # ------------------ LLM ------------------
    llm: LLMConfig = Field(
        default_factory=lambda: LLMConfig(
            provider="alibaba",
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            model="qwen2.5-vl-72b-instruct",
            temperature=0.2,
            max_tokens=1024,
            max_retries=3,
            base_delay=0.5,
            max_context_tokens=4096,
        )
    )

    # ------------------ embeddings ------------------
    embeddings: EmbeddingsConfig = Field(
        default_factory=lambda: EmbeddingsConfig(
            model="text-embedding-v3",
            dimension=1024,
            max_concurrency=5,
            max_retries=3,
            base_delay=0.5,
        )
    )

    # ------------------ vector DB ------------------
    vector_db: VectorDBConfig = Field(
        default_factory=lambda: VectorDBConfig(
            enabled=True,
            table="chunk_embeddings",
        )
    )

    # ------------------ postgres URL ------------------
    @property
    def postgres_full_url(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )
        
def get_config():
    return AppSettings() # type: ignore