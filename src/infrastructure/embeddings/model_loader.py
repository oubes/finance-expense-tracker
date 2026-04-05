# ---- Imports ----
import logging
from openai import OpenAI
from src.core.config.settings import AppSettings

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)


# ---- Model Loader Class ----
class ModelLoader:
    # ---- Constructor ----
    def __init__(self, settings: AppSettings):
        logger.info("Initializing OpenAI ModelLoader")

        self.client = OpenAI(
            api_key=settings.alibaba_api_key,
            base_url=settings.llm.base_url,
        )

        self.embedding_model = settings.embeddings.model

        logger.info("OpenAI client initialized")
        logger.info("Embedding model set to: %s", self.embedding_model)

    # ---- Client Getter ----
    def get_client(self) -> OpenAI:
        logger.debug("get_client called")
        return self.client

    # ---- Embedding Model Getter ----
    def get_embedding_model(self) -> str:
        logger.debug("get_embedding_model called")
        return self.embedding_model