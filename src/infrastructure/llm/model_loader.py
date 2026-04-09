# ---- Imports ----
from openai import AsyncOpenAI
from src.core.config.settings import AppSettings
from src.core.contracts.llm.llm import LLMClientContract


# ---- LLM Client ----
class LLMClient(LLMClientContract):
    # ---- Constructor ----
    def __init__(self, settings: AppSettings):
        self._client = AsyncOpenAI(
            api_key=settings.alibaba_api_key,
            base_url=settings.llm.base_url,
        )
        self._model = settings.llm.model

    # ---- Get Client ----
    def get_client(self) -> AsyncOpenAI:
        return self._client

    # ---- Get Model ----
    def get_model(self) -> str:
        return self._model