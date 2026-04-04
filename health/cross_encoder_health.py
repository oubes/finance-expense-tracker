import time
import asyncio
import logging
from src.infrastructure.cross_encoder.model_loader import ModelLoader
from src.api.v1.schemas.health_schemas import DependencyResult, CrossEncoderHealthData

# Initialize logger
logger = logging.getLogger(__name__)

class CrossEncoderHealth:
    """
    Check Cross-Encoder model health by running a sample prediction.
    """
    def __init__(self, model_loader: ModelLoader | None = None):
        self.model_loader = model_loader or ModelLoader()
        self.model = self.model_loader.get_model()
        self.model_name = self.model_loader.model_name

    async def check(self, timeout: float = 3.0) -> DependencyResult:
        start = time.perf_counter()
        logger.info(f"Starting Cross-Encoder health check for: {self.model_name}")
        
        try:
            async with asyncio.timeout(timeout):
                # Run CPU/GPU bound prediction in executor
                loop = asyncio.get_running_loop()
                test_pairs = [("ping", "pong")]
                await loop.run_in_executor(None, self.model.predict, test_pairs)

            latency = (time.perf_counter() - start) * 1000
            data = CrossEncoderHealthData(
                healthy=True, 
                model=self.model_name, 
                latency_ms=latency,
                device=self.model_loader.device,
            )
            
            logger.info("Cross-Encoder health check successful")
            return DependencyResult(status="success", data=data.model_dump())

        except Exception as e:
            logger.exception("Cross-Encoder health check failed")
            return DependencyResult(
                status="failed",
                error=str(e),
            )