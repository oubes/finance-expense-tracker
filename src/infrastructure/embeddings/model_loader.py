import logging
from openai import OpenAI
from src.core.config.loader import load_settings

logger = logging.getLogger(__name__)


class ModelLoader:
    def __init__(self):
        logger.info("Initializing OpenAI ModelLoader")

        settings = load_settings()

        self.client = OpenAI(
            api_key=settings.alibaba_api_key,
            base_url=settings.llm.base_url,
        )

        self.embedding_model = settings.embeddings.model

        logger.info("OpenAI client initialized")
        logger.info("Embedding model set to: %s", self.embedding_model)

    def get_client(self) -> OpenAI:
        logger.debug("get_client called")
        return self.client

    def get_embedding_model(self) -> str:
        logger.debug("get_embedding_model called")
        return self.embedding_model