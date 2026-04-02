from openai import OpenAI
from src.core.config.loader import load_settings

class ModelLoader:
    def __init__(self):
        settings = load_settings()

        self.client = OpenAI(
            api_key=settings.alibaba_api_key,
            base_url=settings.llm.base_url,
        )

        self.embedding_model = settings.embeddings.model

    def get_client(self) -> OpenAI:
        return self.client

    def get_embedding_model(self) -> str:
        return self.embedding_model