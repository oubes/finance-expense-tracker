# ---- Imports ----
from typing import Any
import logging


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Safe Generator (Orchestrator Only) ----
class SafeGenerator:
    # ---- Constructor ----
    def __init__(
        self,
        msg_builder,
        llm_generator,
        extractor,
        validator,
    ):
        self.msg_builder = msg_builder
        self.llm_generator = llm_generator
        self.extractor = extractor
        self.validator = validator

    # ---- Atomic Pipeline ----
    async def run(
        self,
        prompt_file_name: str,
        required_keys: set[str] | None = None,
        allowed_flags: set[str] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 256,
        **kwargs: Any,
    ) -> dict[str, Any]:

        # ---- Atomic Pipeline ----
        try:
            logger.info(f"[SafeGenerator] Building messages | prompt={prompt_file_name}")

            built = await self.msg_builder.build_async(
                prompt_file_name=prompt_file_name,
                **kwargs,
            )

            if not built.get("state"):
                logger.warning(f"[SafeGenerator] MsgBuilder failed | prompt={prompt_file_name}")
                return {"state": False, "data": None}

            messages = built["data"]

        except Exception as e:
            logger.exception(
                f"[SafeGenerator] MsgBuilder exception | prompt={prompt_file_name} | error={e}"
            )
            return {"state": False, "data": None}

        # ---- Atomic Pipeline ----
        try:
            logger.info(f"[SafeGenerator] LLM generation started | prompt={prompt_file_name}")

            raw = await self.llm_generator.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            logger.info(f"[SafeGenerator] LLM generation success | prompt={prompt_file_name}")

        except Exception as e:
            logger.exception(
                f"[SafeGenerator] LLM generation failed | prompt={prompt_file_name} | error={e}"
            )
            return {"state": False, "data": None}

        # ---- Atomic Pipeline ----
        try:
            logger.info("[SafeGenerator] Extracting JSON from LLM output")

            extracted = await self.extractor.extract_one(raw)

            if not extracted.get("state"):
                logger.warning("[SafeGenerator] JSON extraction failed")
                return {"state": False, "data": None}

            parsed = extracted["data"]

        except Exception as e:
            logger.exception(f"[SafeGenerator] Extractor exception | error={e}")
            return {"state": False, "data": None}

        # ---- Atomic Pipeline ----
        try:
            logger.info("[SafeGenerator] Validating parsed output")

            validated = self.validator.validate_one(
                parsed=parsed,
                required_keys=required_keys,
                allowed_flags=allowed_flags,
            )

            if not validated.get("state"):
                logger.warning("[SafeGenerator] Validation failed")
                return {"state": False, "data": None}

        except Exception as e:
            logger.exception(f"[SafeGenerator] Validator exception | error={e}")
            return {"state": False, "data": None}

        # ---- Atomic Pipeline ----
        logger.info("[SafeGenerator] Pipeline completed successfully")

        return {
            "state": True,
            "data": validated["data"],
        }