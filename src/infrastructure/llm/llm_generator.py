# ---- Imports ----
from src.infrastructure.llm.model_loader import LLMClient
from src.core.contracts.llm.llm import LLMGeneratorContract
import time
import logging

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- LLM Generator Class ----
class LLMGenerator(LLMGeneratorContract):
    # ---- Constructor ----
    def __init__(
        self,
        llm: LLMClient,
        max_retries: int = 3,
        base_delay: float = 0.5,
    ):
        self._llm = llm
        self._max_retries = max_retries
        self._base_delay = base_delay

    # ---- Prompt Safety / Formatting ----
    def _sanitize_messages(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        sanitized: list[dict[str, str]] = []

        for msg in messages:
            role = (msg.get("role") or "").strip()
            content = (msg.get("content") or "").strip()

            if not role or not content:
                continue

            sanitized.append(
                {
                    "role": role,
                    "content": content[:4000],
                }
            )

        return sanitized

    # ---- Text Generation ----
    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 128,
    ) -> str:

        logger.info("LLM generation started")

        safe_messages = self._sanitize_messages(messages)

        client = self._llm.get_client()
        model = self._llm.get_model()

        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1} for model={model}")

                response = client.chat.completions.create(
                    model=model,
                    messages=safe_messages,  # type: ignore
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                result = response.choices[0].message.content or ""

                logger.info("LLM generation succeeded")
                return result

            except Exception as e:
                last_error = e

                # ---- Error Handling ----
                error_msg = str(e).lower()

                logger.warning(
                    f"LLM generation failed on attempt {attempt + 1}: {error_msg}"
                )

                # ---- Rate limit awareness heuristic ----
                if "rate" in error_msg:
                    sleep_time = self._base_delay * (2 ** attempt)
                else:
                    sleep_time = self._base_delay

                time.sleep(sleep_time)

        logger.error("LLM generation failed after all retries")
        raise last_error if last_error else RuntimeError("Unknown failure")