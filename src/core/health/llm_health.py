# ---- Imports ----
import time
import asyncio
import logging
from src.bootstrap.dependencies.llm_dep import get_llm_client
from src.core.schemas.health.health_schemas import DependencyResult, LLMHealthData

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)


# ---- LLM Health Check Class ----
class LLMHealth:
    # ---- Constructor ----
    def __init__(self):
        self.llm_client = get_llm_client()
        self.client = self.llm_client.get_client()
        self.model_name = self.llm_client.get_model()

    # ---- Health Check Execution ----
    async def check(self, timeout: float = 3.0) -> DependencyResult:
        start = time.perf_counter()

        try:
            async with asyncio.timeout(timeout):
                # ---- LLM Request Execution ----
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model_name,
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=1,
                    temperature=0.0,
                )

            # ---- Response Validation ----
            if not response or not response.choices: # type: ignore
                raise ValueError("Empty response from LLM")

            latency = (time.perf_counter() - start) * 1000

            # ---- Health Data Construction ----
            data = LLMHealthData(
                healthy=True,
                model=self.model_name,
                latency_ms=round(latency, 3),
            )

            logger.info("LLM health check successful")

            # ---- Success Response ----
            return DependencyResult(
                status="success",
                data=data.model_dump(),
            )

        except Exception as e:
            logger.exception("LLM health check failed")

            # ---- Failure Response ----
            return DependencyResult(
                status="failed",
                error=str(e),
            )