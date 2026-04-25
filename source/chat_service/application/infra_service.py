# ---- Imports ----
import time
import logging
from typing import Any

logger = logging.getLogger(__name__)


# ---- Base Service ----
class BaseInfraService:

    def __init__(self, name: str):
        self.name = name

    async def _execute(self, fn, *args, **kwargs) -> dict[str, Any]:
        start = time.perf_counter()

        try:
            result = await fn(*args, **kwargs)

            latency_ms = (time.perf_counter() - start) * 1000

            return {
                "status": "up",
                "data": result,
                "error": None,
                "latency_ms": latency_ms,
            }

        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000

            logger.exception(
                f"[{self.name}] request failed",
                extra={
                    "error": str(e),
                },
            )

            return {
                "status": "unreachable",
                "data": None,
                "error": str(e),
                "latency_ms": latency_ms,
            }


# ---- LLM Service ----
class LLMService(BaseInfraService):

    def __init__(self, adapter):
        super().__init__("LLM_SERVICE")
        self.adapter = adapter
        
    async def health_check(self) -> dict[str, Any]:
        return await self._execute(
            self.adapter.health_check,
        )


    async def generate(self, prompt: str, **kwargs) -> dict[str, Any]:
        return await self._execute(
            self.adapter.generate,
            prompt=prompt,
            **kwargs,
        )


# ---- Embedding Service ----
class EmbeddingService(BaseInfraService):

    def __init__(self, adapter):
        super().__init__("EMBEDDING_SERVICE")
        self.adapter = adapter

    async def embed(self, texts: list[str]) -> dict[str, Any]:
        return await self._execute(
            self.adapter.embed_batch,
            texts=texts,
        )


# ---- VectorDB Service ----
class VectorDBService(BaseInfraService):

    def __init__(self, adapter):
        super().__init__("VECTOR_DB_SERVICE")
        self.adapter = adapter

    async def upsert(self, vectors: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._execute(
            self.adapter.upsert,
            vectors=vectors,
        )

    async def search(self, query_vector: list[float], top_k: int = 5) -> dict[str, Any]:
        return await self._execute(
            self.adapter.search,
            query_vector=query_vector,
            top_k=top_k,
        )