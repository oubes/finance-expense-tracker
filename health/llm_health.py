import time
import asyncio
import logging
from src.bootstrap.dependencies import get_llm_client
from src.core.health.schemas.health_schemas import DependencyResult, LLMHealthData

logger = logging.getLogger(__name__)


class LLMHealth:
    def __init__(self):
        self.client = get_llm_client()
        self.model_name = self.client.model

    async def check(self, timeout: float = 3.0) -> DependencyResult:
        start = time.perf_counter()

        try:
            async with asyncio.timeout(timeout):
                response = await asyncio.to_thread(
                    self.client.client.chat.completions.create,
                    model=self.model_name,
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=1,
                    temperature=0.0,
                )

            if not response or not response.choices:
                raise ValueError("Empty response from LLM")

            latency = (time.perf_counter() - start) * 1000

            data = LLMHealthData(
                healthy=True,
                model=self.model_name,
                latency_ms=latency,
            )

            logger.info("LLM health check successful")

            return DependencyResult(
                status="success",
                data=data.model_dump(),
            )

        except Exception as e:
            logger.exception("LLM health check failed")

            return DependencyResult(
                status="failed",
                error=str(e),
            )