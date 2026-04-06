# ---- Imports ----
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---- Sub Models ----
class LLMConfig(BaseModel):
    provider: str
    base_url: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 256

class ingestionConfig(BaseModel):
    chunk_size: int
    chunk_overlap: int
    prompt_templates_dir: str

class EmbeddingsConfig(BaseModel):
    model: str
    dimension: int


class RAGConfig(BaseModel):
    top_k_retrieval: int
    top_k_rerank: int
    cross_encoder_model: str


class VectorDBConfig(BaseModel):
    enabled: bool
    table: str


class RateLimitConfig(BaseModel):
    requests: int
    window_seconds: int


class ObservabilityConfig(BaseModel):
    metrics_enabled: bool
    tracing_enabled: bool
    otel_exporter_endpoint: str


class DatabaseConfig(BaseModel):
    host: str
    port: int
    db: str
    user: str
    password: str
    full_url: str
    type: str


class RedisConfig(BaseModel):
    host: str
    port: int
    db: int
    password: str | None = None
    full_url: str


# ---- Root Settings ----
class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- App ----
    app_name: str = Field(alias="APP_NAME")
    app_env: str = Field(alias="APP_ENV")
    debug: bool = Field(alias="DEBUG")
    log_level: str = Field(alias="LOG_LEVEL")

    # ---- Server ----
    host: str = Field(alias="HOST")
    port: int = Field(alias="PORT")

    # ---- Security ----
    secret_key: str = Field(alias="SECRET_KEY")

    # ---- External APIs ----
    alibaba_api_key: str | None = Field(alias="ALIBABA_API_KEY", default=None)

    # ---- Flat DB ENV ----
    postgres_host: str = Field(alias="POSTGRES_HOST")
    postgres_port: int = Field(alias="POSTGRES_PORT")
    postgres_db: str = Field(alias="POSTGRES_DB")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")
    postgres_db_type: str = Field(alias="POSTGRES_DB_TYPE")

    # ---- Postgres URL Builder ----
    @property
    def postgres_full_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:"
            f"{self.postgres_password}@"
            f"{self.postgres_host}:"
            f"{self.postgres_port}/"
            f"{self.postgres_db}"
        )

    # ---- Flat Redis ENV ----
    redis_host: str = Field(alias="REDIS_HOST")
    redis_port: int = Field(alias="REDIS_PORT")
    redis_db: int = Field(alias="REDIS_DB")
    redis_password: str | None = Field(alias="REDIS_PASSWORD", default=None)

    # ---- Redis URL Builder ----
    @property
    def redis_full_url(self) -> str:
        auth_part = f":{self.redis_password}@" if self.redis_password else ""

        return (
            f"redis://{auth_part}"
            f"{self.redis_host}:"
            f"{self.redis_port}/"
            f"{self.redis_db}"
        )

    # ---- Structured configs (from YAML) ----
    llm: LLMConfig
    ingestion: ingestionConfig
    embeddings: EmbeddingsConfig
    rag: RAGConfig
    vector_db: VectorDBConfig
    rate_limit: RateLimitConfig
    observability: ObservabilityConfig

    # ---- Infra configs (built from ENV) ----
    database: DatabaseConfig | None = None
    redis: RedisConfig | None = None

    # ---- Post Init Hook ----
    def model_post_init(self, __context):
        self.database = DatabaseConfig(
            host=self.postgres_host,
            port=self.postgres_port,
            db=self.postgres_db,
            user=self.postgres_user,
            password=self.postgres_password,
            full_url=self.postgres_full_url,
            type=self.postgres_db_type,
        )

        self.redis = RedisConfig(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            password=self.redis_password,
            full_url=self.redis_full_url,
        )