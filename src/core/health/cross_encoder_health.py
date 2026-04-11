# ---- Imports ----
import time
import asyncio
import logging
from src.bootstrap.dependencies.cross_encoder_dep import get_cross_encoder
from src.core.schemas.health.health_schemas import DependencyResult, CrossEncoderHealthData

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)


# ---- CrossEncoder Health Check Class ----
class CrossEncoderHealth:
    # ---- Constructor ----
    def __init__(self):
        self.cross_encoder = get_cross_encoder()
        self.model_name = self.cross_encoder.model_loader.model_name

    # ---- Health Check Execution ----
    async def check(self, timeout: float = 3.0) -> DependencyResult:
        start = time.perf_counter()

        try:
            async with asyncio.timeout(timeout):
                loop = asyncio.get_running_loop()

                # ---- Test Input ----
                test_pairs = [("ping", "pong")]

                # ---- Model Inference Execution ----
                await loop.run_in_executor(
                    None,
                    self.cross_encoder.model.predict,
                    test_pairs,
                )

            latency = (time.perf_counter() - start) * 1000

            # ---- Health Data Construction ----
            data = CrossEncoderHealthData(
                healthy=True,
                model=self.model_name,
                latency_ms=round(latency, 3),
                device=self.cross_encoder.model_loader.device,
            )

            logger.info("Cross-Encoder health check successful")

            # ---- Success Response ----
            return DependencyResult(
                status="success",
                data=data.model_dump(),
            )

        except Exception as e:
            logger.exception("Cross-Encoder health check failed")

            # ---- Failure Response ----
            return DependencyResult(
                status="failed",
                error=str(e),
            )