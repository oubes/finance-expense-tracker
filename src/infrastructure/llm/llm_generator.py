from src.infrastructure.llm.model_loader import LLMClient


class LLMGenerator:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate(
        self,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int = 128,
    ) -> str:

        return self.llm.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
