import time
import asyncio
import logging
from pydantic import BaseModel
from src.infrastructure.cross_encoder.model_loader import ModelLoader

logger = logging.getLogger(__name__)


class CrossEncoderHealthStatus(BaseModel):
    healthy: bool
    model: str | None = None
    latency_ms: float | None = None
    detail: str | None = None


class CrossEncoderHealth:
    def __init__(self, model_loader: ModelLoader | None = None):
        logger.info("Initializing CrossEncoderHealth")
        self.model_loader = model_loader or ModelLoader()
        self.model = self.model_loader.get_model()
        self.model_name = self.model_loader.model_name
        logger.info("CrossEncoderHealth initialized successfully")

    async def check(self, timeout: float = 2.0) -> CrossEncoderHealthStatus:
        start = time.perf_counter()
        logger.info("Starting CrossEncoder health check")

        try:
            async with asyncio.timeout(timeout):
                loop = asyncio.get_running_loop()
                test_pairs = [("hello", "hello world")]

                _ = await loop.run_in_executor(
                    None,
                    self.model.predict,
                    test_pairs
                )

            latency = (time.perf_counter() - start) * 1000

            result = CrossEncoderHealthStatus(
                healthy=True,
                model=self.model_name,
                latency_ms=latency,
                detail="ok",
            )

            logger.info("CrossEncoder health check successful | latency_ms=%.2f", latency)
            return result

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000

            logger.exception("CrossEncoder health check failed | latency_ms=%.2f", latency)

            return CrossEncoderHealthStatus(
                healthy=False,
                model=self.model_name,
                latency_ms=latency,
                detail=str(e),
            )