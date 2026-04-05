# ---- Imports ----
from src.infrastructure.llm.model_loader import LLMClient
from src.core.contracts.llm.llm import LLMGeneratorContract


# ---- LLM Generator Class ----
class LLMGenerator(LLMGeneratorContract):
    # ---- Constructor ----
    def __init__(self, llm: LLMClient):
        self._llm = llm

    # ---- Text Generation ----
    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 128,
    ) -> str:

        client = self._llm.get_client()
        model = self._llm.get_model()

        response = client.chat.completions.create(
            model=model,
            messages=messages, # type: ignore
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content or ""