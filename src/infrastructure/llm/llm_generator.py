# ---- Imports ----
from src.infrastructure.llm.model_loader import LLMClient
from src.core.contracts.llm.llm import LLMGeneratorContract
from src.core.config.settings import AppSettings
import asyncio
import logging

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- LLM Generator Class ----
class LLMGenerator(LLMGeneratorContract):
    # ---- Constructor ----
    def __init__(
        self,
        llm: LLMClient,
        settings: AppSettings,
    ):
        self._llm = llm
        self._config = settings
        self._max_retries = self._config.llm.max_retries
        self._base_delay = self._config.llm.base_delay
        self._max_context_tokens = self._config.llm.max_context_tokens

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
                    "content": content[:self._max_context_tokens],
                }
            )

        return sanitized

    # ---- Text Generation ----
    async def generate(
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

                response = await client.chat.completions.create(
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

                error_msg = str(e).lower()

                logger.warning(
                    f"LLM generation failed on attempt {attempt + 1}: {error_msg}"
                )

                if "rate" in error_msg:
                    sleep_time = self._base_delay * (2 ** attempt)
                else:
                    sleep_time = self._base_delay

                await asyncio.sleep(sleep_time)

        logger.error("LLM generation failed after all retries")
        raise last_error if last_error else RuntimeError("Unknown failure")