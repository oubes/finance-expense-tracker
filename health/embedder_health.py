from src.infrastructure.embeddings.model_loader import ModelLoader
from src.infrastructure.embeddings.embedder import Embedder


class EmbedderHealth:
    def __init__(self):
        self.model_loader = ModelLoader()
        self.embedder = Embedder(self.model_loader)

    async def check(self):
        try:
            # lightweight test embedding
            test_text = "health_check"

            embedding = self.embedder.embed(test_text)

            if not embedding or not isinstance(embedding, list):
                return {
                    "healthy": False,
                    "error": "Invalid embedding response"
                }

            return {
                "healthy": True,
                "model": self.model_loader.get_embedding_model(),
                "dimension": len(embedding),
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }