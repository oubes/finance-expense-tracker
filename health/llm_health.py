import time
import asyncio
import logging

from src.infrastructure.llm.model_loader import LLMClient
from src.api.v1.schemas.health_schemas import DependencyStatus

logger = logging.getLogger(__name__)

# Checks LLM health and returns status with model info
class LLMHealth:
    def __init__(self):
        self.client = LLMClient()
        self.model_name = self.client.model

    # Run health check request
    async def check(self, timeout: float = 2.0) -> DependencyStatus:
        start = time.perf_counter()

        logger.info(
            "LLM health check started",
            extra={"model": self.model_name, "timeout": timeout},
        )

        try:
            response = await self._call_with_timeout(timeout)

            self._validate_response(response)

            latency = self._calculate_latency(start)

            logger.info(
                "LLM health check success",
                extra={
                    "model": self.model_name,
                    "latency_ms": latency,
                },
            )

            return self._build_success(latency)

        except Exception as e:
            latency = self._calculate_latency(start)

            logger.error(
                "LLM health check failed",
                extra={
                    "model": self.model_name,
                    "latency_ms": latency,
                    "error": str(e),
                },
            )

            return self._build_failure(str(e), latency)

    # Execute LLM call with timeout
    async def _call_with_timeout(self, timeout: float):
        async with asyncio.timeout(timeout):
            return await asyncio.to_thread(
                self.client.client.chat.completions.create,
                model=self.model_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
                temperature=0.0,
            )

    # Validate LLM response structure
    def _validate_response(self, response):
        if (
            not response
            or not response.choices
            or not response.choices[0].message
            or not response.choices[0].message.content
        ):
            raise ValueError("Empty or invalid response")

    # Compute latency in ms
    def _calculate_latency(self, start: float) -> float:
        return (time.perf_counter() - start) * 1000

    # Build success response
    def _build_success(self, latency: float) -> DependencyStatus:
        return DependencyStatus(
            healthy=True,
            detail="ok",
            latency_ms=latency,
            model=self.model_name,
        )

    # Build failure response
    def _build_failure(self, error: str, latency: float) -> DependencyStatus:
        return DependencyStatus(
            healthy=False,
            detail=error,
            latency_ms=latency,
            model=self.model_name,
        )