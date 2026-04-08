# ---- Imports ----
import logging
import asyncio

from src.core.contracts.embeddings.embedder import EmbedderContract
from src.infrastructure.embeddings.model_loader import ModelLoader

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)


# ---- Embedder Class ----
class Embedder(EmbedderContract):

    # ---- Constructor ----
    def __init__(self, model_loader: ModelLoader, max_concurrency: int = 5):
        logger.info("Initializing Embedder")

        self.model_loader = model_loader
        self.client = self.model_loader.get_client()
        self.model = self.model_loader.get_embedding_model()

        self.semaphore = asyncio.Semaphore(max_concurrency)

        logger.info("Embedder initialized using model: %s", self.model)

    # ---- Single Text Embedding ----
    async def embed(self, text: str) -> list[float]:
        async with self.semaphore:
            response = await asyncio.to_thread(
                self.client.embeddings.create,
                model=self.model,
                input=text
            )
            return response.data[0].embedding

    # ---- Internal Batch Worker ----
    async def _embed_batch_worker(self, batch: list[str]) -> list[list[float]]:
        async with self.semaphore:
            response = await asyncio.to_thread(
                self.client.embeddings.create,
                model=self.model,
                input=batch
            )
            return [item.embedding for item in response.data]

    # ---- Batch Embedding (Parallelized) ----
    async def embed_batch(self, texts: list[str], batch_size: int = 10) -> list[list[float]]:
        logger.debug("Embedding batch of size: %d", len(texts))

        batches: list[list[str]] = [
            texts[i:i + batch_size]
            for i in range(0, len(texts), batch_size)
        ]

        tasks = [self._embed_batch_worker(batch) for batch in batches]

        results = await asyncio.gather(*tasks)

        all_embeddings: list[list[float]] = []
        for batch_result in results:
            all_embeddings.extend(batch_result)

        logger.debug("Batch embedding completed with %d batches", len(batches))
        return all_embeddings