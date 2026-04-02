from src.infrastructure.llm.model_loader import ModelLoader


class LLMHealth:
    def __init__(self):
        self.model_loader = ModelLoader()
        self.client = self.model_loader.get_client()

    async def check(self):
        try:
            response = self.client.chat.completions.create(
                model=self.model_loader.get_model_name(),
                messages=[
                    {"role": "user", "content": "ping"}
                ],
                max_tokens=1
            )

            if not response or not response.choices:
                return {
                    "healthy": False,
                    "error": "Empty response"
                }

            return {
                "healthy": True,
                "model": self.model_loader.get_model_name(),
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }