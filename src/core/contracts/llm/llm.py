# ---- Imports ----
from abc import ABC, abstractmethod

# ---- LLM Client Interface ----
class LLMClientContract(ABC):
    # ---- Get underlying client ----
    @abstractmethod
    def get_client(self):
        pass

    # ---- Get default model name ----
    @abstractmethod
    def get_model(self) -> str:
        pass
    

# ---- LLM Generator Interface ----
class LLMGeneratorContract(ABC):
    # ---- Text Generation ----
    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 128,
    ) -> str:
        pass