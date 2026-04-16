# ---- Imports ----
from openai import AsyncOpenAI
from source.infra_service.core.config.settings import AppSettings


# ---- LLM Client ----
class LLMClient:

    # ---- Constructor ----
    def __init__(self, settings: AppSettings):
        self._client = AsyncOpenAI(
            api_key=settings.ALIBABA_API_KEY,
            base_url=settings.llm.base_url,
        )
        self._model = settings.llm.model

    # ---- Get Client ----
    def get_client(self) -> AsyncOpenAI:
        return self._client

    # ---- Get Model ----
    def get_model(self) -> str:
        return self._model