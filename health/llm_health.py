import time
import asyncio
import logging

from src.infrastructure.llm.model_loader import LLMClient
from src.api.v1.schemas.health_schemas import DependencyStatus


logger = logging.getLogger(__name__)


class LLMHealth:
    def __init__(self):
        self.client = LLMClient()

    async def check(self, timeout: float = 2.0) -> DependencyStatus:
        start = time.perf_counter()

        logger.info(
            "LLM health check started",
            extra={"model": self.client.model, "timeout": timeout},
        )

        try:
            async with asyncio.timeout(timeout):
                response = await asyncio.to_thread(
                    self.client.client.chat.completions.create,
                    model=self.client.model,
                    messages=[
                        {"role": "user", "content": "ping"}
                    ],
                    max_tokens=1,
                    temperature=0.0,
                )

            # Validate response
            if (
                not response
                or not response.choices
                or not response.choices[0].message
                or not response.choices[0].message.content
            ):
                raise ValueError("Empty or invalid response")

            latency = (time.perf_counter() - start) * 1000

            logger.info(
                "LLM health check success",
                extra={
                    "model": self.client.model,
                    "latency_ms": latency,
                },
            )

            return DependencyStatus(
                healthy=True,
                detail=f"ok (model={self.client.model})",
                latency_ms=latency,
            )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000

            logger.error(
                "LLM health check failed",
                extra={
                    "model": self.client.model,
                    "latency_ms": latency,
                    "error": str(e),
                },
            )

            return DependencyStatus(
                healthy=False,
                detail=str(e),
                latency_ms=latency,
            )