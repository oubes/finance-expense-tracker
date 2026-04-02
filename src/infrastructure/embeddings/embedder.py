from src.infrastructure.embeddings.model_loader import ModelLoader

class Embedder:
    def __init__(self, model_loader: ModelLoader | None = None):
        self.model_loader = model_loader or ModelLoader()

        self.client = self.model_loader.get_client()
        self.model = self.model_loader.get_embedding_model()

    def embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]
    
print(Embedder().embed("Hello world!"))