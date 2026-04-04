import time
import asyncio
import logging
from src.bootstrap.dependencies import get_cross_encoder
from src.api.v1.schemas.health_schemas import DependencyResult, CrossEncoderHealthData

logger = logging.getLogger(__name__)


class CrossEncoderHealth:
    def __init__(self):
        self.cross_encoder = get_cross_encoder()
        self.model_name = self.cross_encoder.model_loader.model_name

    async def check(self, timeout: float = 3.0) -> DependencyResult:
        start = time.perf_counter()

        try:
            async with asyncio.timeout(timeout):
                loop = asyncio.get_running_loop()
                test_pairs = [("ping", "pong")]

                await loop.run_in_executor(
                    None,
                    self.cross_encoder.model.predict,
                    test_pairs,
                )

            latency = (time.perf_counter() - start) * 1000

            data = CrossEncoderHealthData(
                healthy=True,
                model=self.model_name,
                latency_ms=latency,
                device=self.cross_encoder.model_loader.device,
            )

            logger.info("Cross-Encoder health check successful")

            return DependencyResult(
                status="success",
                data=data.model_dump(),
            )

        except Exception as e:
            logger.exception("Cross-Encoder health check failed")

            return DependencyResult(
                status="failed",
                error=str(e),
            )