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
    def __init__(self, model_loader: ModelLoader, max_concurrency: int = 5, max_retries: int = 3, base_delay: float = 0.5):
        logger.info("Initializing Embedder")

        self.model_loader = model_loader
        self.client = self.model_loader.get_client()
        self.model = self.model_loader.get_embedding_model()

        self.semaphore = asyncio.Semaphore(max_concurrency)

        # ---- Retry Config ----
        self._max_retries = max_retries
        self._base_delay = base_delay

        logger.info("Embedder initialized using model: %s", self.model)

    # ---- Prompt Safety / Formatting ----
    def _sanitize_texts(self, texts: list[str]) -> list[str]:
        sanitized: list[str] = []

        for text in texts:
            clean = (text or "").strip()
            if not clean:
                continue

            sanitized.append(clean[:4000])  # prevent oversized inputs

        return sanitized

    # ---- Single Text Embedding ----
    async def embed(self, text: str) -> list[float]:
        safe_text = self._sanitize_texts([text])[0]

        async with self.semaphore:
            last_error: Exception | None = None

            for attempt in range(self._max_retries):
                try:
                    logger.debug(f"Embedding single text attempt {attempt + 1}")

                    response = await asyncio.to_thread(
                        self.client.embeddings.create,
                        model=self.model,
                        input=safe_text,
                    )

                    logger.info("Single embedding succeeded")
                    return response.data[0].embedding

                except Exception as e:
                    last_error = e
                    error_msg = str(e).lower()

                    logger.warning(
                        f"Single embedding failed attempt {attempt + 1}: {error_msg}"
                    )

                    if "rate" in error_msg:
                        sleep_time = self._base_delay * (2 ** attempt)
                    else:
                        sleep_time = self._base_delay

                    await asyncio.sleep(sleep_time)

            logger.error("Single embedding failed after all retries")
            raise last_error if last_error else RuntimeError("Unknown failure")

    # ---- Internal Batch Worker ----
    async def _embed_batch_worker(self, batch: list[str]) -> list[list[float]]:
        safe_batch = self._sanitize_texts(batch)

        async with self.semaphore:
            last_error: Exception | None = None

            for attempt in range(self._max_retries):
                try:
                    logger.debug(f"Batch worker attempt {attempt + 1} | batch_size={len(safe_batch)}")

                    response = await asyncio.to_thread(
                        self.client.embeddings.create,
                        model=self.model,
                        input=safe_batch,
                    )

                    logger.info("Batch embedding worker succeeded")
                    return [item.embedding for item in response.data]

                except Exception as e:
                    last_error = e
                    error_msg = str(e).lower()

                    logger.warning(
                        f"Batch embedding failed attempt {attempt + 1}: {error_msg}"
                    )

                    if "rate" in error_msg:
                        sleep_time = self._base_delay * (2 ** attempt)
                    else:
                        sleep_time = self._base_delay

                    await asyncio.sleep(sleep_time)

            logger.error("Batch worker failed after all retries")
            raise last_error if last_error else RuntimeError("Unknown failure")

    # ---- Batch Embedding (Parallelized) ----
    async def embed_batch(self, texts: list[str], batch_size: int = 10) -> list[list[float]]:
        logger.info("Batch embedding started | total=%d", len(texts))

        sanitized_texts = self._sanitize_texts(texts)

        batches: list[list[str]] = [
            sanitized_texts[i:i + batch_size]
            for i in range(0, len(sanitized_texts), batch_size)
        ]

        tasks = [self._embed_batch_worker(batch) for batch in batches]

        results = await asyncio.gather(*tasks)

        all_embeddings: list[list[float]] = []
        for batch_result in results:
            all_embeddings.extend(batch_result)

        logger.info("Batch embedding completed | batches=%d", len(batches))
        return all_embeddings