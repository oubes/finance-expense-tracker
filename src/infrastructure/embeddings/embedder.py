# ---- Imports ----
import logging
from src.core.contracts.embeddings.embedder import EmbedderContract
from src.infrastructure.embeddings.model_loader import ModelLoader

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)


# ---- Embedder Class ----
class Embedder(EmbedderContract):
    # ---- Constructor ----
    def __init__(self, model_loader: ModelLoader):
        logger.info("Initializing Embedder")
        self.model_loader = model_loader

        self.client = self.model_loader.get_client()
        self.model = self.model_loader.get_embedding_model()

        logger.info("Embedder initialized using model: %s", self.model)

    # ---- Single Text Embedding ----
    def embed(self, text: str) -> list[float]:
        logger.debug("Embedding single text")
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        embedding = response.data[0].embedding
        logger.debug("Single embedding generated")
        return embedding

    # ---- Batch Embedding (with batching constraint handling) ----
    def embed_batch(self, texts: list[str], batch_size: int = 10) -> list[list[float]]:
        logger.debug("Embedding batch of size: %d", len(texts))

        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            response = self.client.embeddings.create(
                model=self.model,
                input=batch
            )

            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        logger.debug("Batch embedding completed")
        return all_embeddings