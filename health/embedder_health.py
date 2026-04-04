import logging
import time
from src.infrastructure.embeddings.model_loader import ModelLoader
from src.infrastructure.embeddings.embedder import Embedder
from src.api.v1.schemas.health_schemas import DependencyResult, EmbedderHealthData

# Initialize logger
logger = logging.getLogger(__name__)

class EmbedderHealth:
    """
    Verify Embedder functionality by generating a test vector.
    """
    def __init__(self):
        self.model_loader = ModelLoader()
        self.embedder = Embedder(self.model_loader)

    async def check(self) -> DependencyResult:
        start_time = time.perf_counter()
        logger.info("Starting Embedder health check")
        
        try:
            # Perform a test embedding
            embedding = self.embedder.embed("health_check")
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            if not isinstance(embedding, list) or len(embedding) == 0:
                raise ValueError("Embedder returned an empty or invalid vector")

            data = EmbedderHealthData(
                healthy=True,
                model=self.model_loader.get_embedding_model(),
                dimension=len(embedding),
                latency_ms=latency_ms
            )
            
            logger.info("Embedder health check successful")
            return DependencyResult(status="success", data=data.model_dump())

        except Exception as e:
            logger.exception("Embedder health check failed")
            return DependencyResult(
                status="failed",
                error=str(e),
            )