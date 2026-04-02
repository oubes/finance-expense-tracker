from openai import OpenAI
from src.core.config.loader import load_settings

class LLMClient:
    def __init__(self):
        settings = load_settings()

        self.client = OpenAI(
            api_key=settings.alibaba_api_key,
            base_url=settings.llm.base_url,
        )
        self.model = settings.llm.model

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 128
    ) -> str:

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content  # type: ignore