import time
import logging
from src.bootstrap.dependencies import get_embedding_model, get_settings
from src.infrastructure.embeddings.embedder import Embedder
from src.api.v1.schemas.health_schemas import DependencyResult, EmbedderHealthData

logger = logging.getLogger(__name__)


class EmbedderHealth:
    def __init__(self):
        self.embedding_model = get_embedding_model()
        self.settings = get_settings()

        self.embedder = Embedder(self.embedding_model)

        self.model_name = (
            self.settings.embeddings.model
        )

    async def check(self) -> DependencyResult:
        start_time = time.perf_counter()

        try:
            embedding = self.embedder.embed("health_check")

            latency_ms = (time.perf_counter() - start_time) * 1000

            if not isinstance(embedding, list) or len(embedding) == 0:
                raise ValueError("Invalid embedding output")

            data = EmbedderHealthData(
                healthy=True,
                model=self.model_name,
                dimension=len(embedding),
                latency_ms=latency_ms,
            )

            logger.info("Embedder health check successful")

            return DependencyResult(
                status="success",
                data=data.model_dump(),
            )

        except Exception as e:
            logger.exception("Embedder health check failed")

            return DependencyResult(
                status="failed",
                error=str(e),
            )