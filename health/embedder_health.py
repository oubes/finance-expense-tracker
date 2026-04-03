import logging
import time

from src.infrastructure.embeddings.model_loader import ModelLoader
from src.infrastructure.embeddings.embedder import Embedder

logger = logging.getLogger(__name__)


class EmbedderHealth:
    def __init__(self):
        self.model_loader = ModelLoader()
        self.embedder = Embedder(self.model_loader)

    async def check(self) -> dict:
        logger.info("Starting embedder health check")

        start_time = time.perf_counter()

        try:
            # lightweight test embedding
            test_text = "health_check"
            logger.debug(f"Embedding test text: {test_text}")

            embedding = self.embedder.embed(test_text)

            latency_ms = (time.perf_counter() - start_time) * 1000

            # validate embedding
            if not isinstance(embedding, list) or len(embedding) == 0:
                logger.error("Invalid embedding response received")
                return {
                    "healthy": False,
                    "error": "Invalid embedding response",
                    "latency_ms": latency_ms,
                }

            result = {
                "healthy": True,
                "model": self.model_loader.get_embedding_model(),
                "dimension": len(embedding),
                "latency_ms": latency_ms,
            }

            logger.info(f"Embedder health check successful: {result}")
            return result

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000

            logger.exception("Embedder health check failed")
            return {
                "healthy": False,
                "error": str(e),
                "latency_ms": latency_ms,
            }