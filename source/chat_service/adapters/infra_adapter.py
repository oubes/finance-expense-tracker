# ---- Imports ----
import logging

from source.chat_service.core.config.settings import AppSettings
from source.chat_service.adapters.base_adapter import BaseAPIClient
from source.chat_service.core.errors.exceptions import ServiceUnavailableException

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---------- Base Infra Client ----------
class BaseInfraClient(BaseAPIClient):
    service_name: str = "infra"

    async def health(self, path: str) -> dict:
        try:
            return await self.get(path, timeout=3.0)

        except Exception:
            logger.error("%s health_check failed", self.service_name)
            raise ServiceUnavailableException(f"{self.service_name} service is not responding")


# ---------- LLM Client ----------
class LLMClient(BaseInfraClient):
    service_name = "LLM"

    def __init__(self, settings: AppSettings) -> None:
        super().__init__(
            base_url=settings.INFRA_SERVICE_URL,
            settings=settings,
        )

    async def health_check(self) -> dict:
        return await self.health("/api/infra/llm/health")


# ---------- Embedding Client ----------
class EmbeddingClient(BaseInfraClient):
    service_name = "Embedding"

    def __init__(self, settings: AppSettings) -> None:
        super().__init__(
            base_url=settings.INFRA_SERVICE_URL,
            settings=settings,
        )

    async def health_check(self) -> dict:
        return await self.health("/api/infra/embedding/health")


# ---------- VectorDB Client ----------
class VectorDBClient(BaseInfraClient):
    service_name = "VectorDB"

    def __init__(self, settings: AppSettings) -> None:
        super().__init__(
            base_url=settings.INFRA_SERVICE_URL,
            settings=settings,
        )

    async def health_check(self) -> dict:
        return await self.health("/api/infra/vectordb/health")