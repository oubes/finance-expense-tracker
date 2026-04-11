# ---- Imports ----
import time
import logging
from src.bootstrap.dependencies.embeddings_dep import get_embedding_model, get_settings
from src.infrastructure.embeddings.embedder import Embedder
from src.core.schemas.health.health_schemas import DependencyResult, EmbedderHealthData

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)


# ---- Embedder Health Check Class ----
class EmbedderHealth:
    # ---- Constructor ----
    def __init__(self):
        self.embedding_model = get_embedding_model()
        self.settings = get_settings()

        self.embedder = Embedder(self.embedding_model)

        self.model_name = self.settings.embeddings.model

    # ---- Health Check Execution ----
    async def check(self) -> DependencyResult:
        start_time = time.perf_counter()

        try:
            # ---- Embedding Generation ----
            embedding = self.embedder.embed("health_check")

            latency = (time.perf_counter() - start_time) * 1000

            # ---- Output Validation ----
            if not isinstance(embedding, list) or len(embedding) == 0:
                raise ValueError("Invalid embedding output")

            # ---- Health Data Construction ----
            data = EmbedderHealthData(
                healthy=True,
                model=self.model_name,
                dimension=len(embedding),
                latency_ms=round(latency, 3),
            )

            logger.info("Embedder health check successful")

            # ---- Success Response ----
            return DependencyResult(
                status="success",
                data=data.model_dump(),
            )

        except Exception as e:
            logger.exception("Embedder health check failed")

            # ---- Failure Response ----
            return DependencyResult(
                status="failed",
                error=str(e),
            )