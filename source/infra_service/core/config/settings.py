from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class LLMConfig(BaseSettings):
    provider: str
    base_url: str
    model: str
    temperature: float = Field(0.1, ge=0.0, le=1.0)  # Ensure it's between 0 and 1
    max_tokens: int = Field(256, gt=0)
    max_retries: int = Field(3, gt=0)
    base_delay: float = Field(0.5, gt=0.0)
    max_context_tokens: int = Field(4096, gt=0)
    
class EmbeddingsConfig(BaseSettings):
    model: str
    dimension: int = Field(1024, gt=0)
    
class DBPoolConfig(BaseSettings):
    min_size: int = Field(10, gt=0)
    max_size: int = Field(25, gt=0)
    timeout: int = Field(30, gt=0)  # seconds
    max_idle: int = Field(300, gt=0)  # seconds
    max_lifetime: int = Field(3600, gt=0)  # seconds
    
class VectorDBConfig(BaseSettings):
    enabled: bool
    table: str

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

    # ---- External APIs ----
    ALIBABA_API_KEY: str | None = Field(alias="ALIBABA_API_KEY", default=None)

    # ---- Flat DB ENV ----
    POSTGRES_HOST: str = Field(alias="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(alias="POSTGRES_PORT")
    POSTGRES_DB: str = Field(alias="POSTGRES_DB")
    POSTGRES_USER: str = Field(alias="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(alias="POSTGRES_PASSWORD")
    POSTGRES_DB_TYPE: str = Field(alias="POSTGRES_DB_TYPE")
    db_pool: DBPoolConfig = DBPoolConfig(
        min_size=10,
        max_size=25,
        timeout=30,
        max_idle=300,
        max_lifetime=3600,
    )
    # ---- Postgres URL Builder ----
    @property
    def postgres_full_url(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )
        
    # ---- LLM Config ----
    llm: LLMConfig = LLMConfig(
        provider="alibaba",
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        model="qwen2.5-vl-72b-instruct",
        temperature=0.2,
        max_tokens=1024,
        max_retries=3,
        base_delay=0.5,
        max_context_tokens=4096,
    )
    
    embeddings: EmbeddingsConfig = EmbeddingsConfig(
        model="text-embedding-v3",
        dimension=1024,
    )
    
    vector_db: VectorDBConfig = VectorDBConfig(
        enabled=True,
        table="chunk_embeddings",
    )
    
    
    