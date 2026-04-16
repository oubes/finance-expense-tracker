# ---- Imports ----
import logging
from openai import AsyncOpenAI
from source.infra_service.core.config.settings import AppSettings

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)


# ---- Embedding Client ----
class EmbeddingClient:

    # ---- Constructor ----
    def __init__(self, settings: AppSettings):
        logger.info("Initializing Async OpenAI EmbeddingClient")

        self._client = AsyncOpenAI(
            api_key=settings.ALIBABA_API_KEY,
            base_url=settings.llm.base_url,
        )

        self._model = settings.embeddings.model

        logger.info("Embedding client initialized")
        logger.info("Embedding model set to: %s", self._model)

    # ---- Get Client ----
    def get_client(self) -> AsyncOpenAI:
        return self._client

    # ---- Get Model ----
    def get_model(self) -> str:
        return self._model