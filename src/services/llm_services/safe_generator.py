# ---- Imports ----
import logging
from typing import Any

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Safe Generator ----
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

    # ---- Build Messages ----
    async def build_messages(
        self,
        prompt_file_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        try:
            logger.info(f"[build_messages] prompt={prompt_file_name}")

            result = await self.msg_builder.build_async(
                prompt_file_name=prompt_file_name,
                **kwargs,
            )

            if not result.get("state"):
                logger.warning("[build_messages] failed")
                return {"state": False, "data": None}

            return result

        except Exception as e:
            logger.exception(f"[build_messages] exception | error={e}")
            return {"state": False, "data": None}

    # ---- Generate LLM ----
    async def generate_llm(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        try:
            logger.info("[generate_llm] start")

            raw = await self.llm_generator.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return {"state": True, "data": raw}

        except Exception as e:
            logger.exception(f"[generate_llm] exception | error={e}")
            return {"state": False, "data": None}

    # ---- Extract JSON ----
    async def extract_json(
        self,
        raw: str,
    ) -> dict[str, Any]:
        try:
            logger.info("[extract_json] start")

            result = await self.extractor.extract_one(raw)

            if not result.get("state"):
                logger.warning("[extract_json] failed")
                return {"state": False, "data": None}

            return result

        except Exception as e:
            logger.exception(f"[extract_json] exception | error={e}")
            return {"state": False, "data": None}

    # ---- Validate Output ----
    def validate_output(
        self,
        parsed: dict,
        required_keys: set[str] | None,
        allowed_flags: set[str] | None,
    ) -> dict[str, Any]:
        try:
            logger.info("[validate_output] start")

            result = self.validator.validate_one(
                parsed=parsed,
                required_keys=required_keys,
                allowed_flags=allowed_flags,
            )

            if not result.get("state"):
                logger.warning("[validate_output] failed")
                return {"state": False, "data": None}

            return result

        except Exception as e:
            logger.exception(f"[validate_output] exception | error={e}")
            return {"state": False, "data": None}

    # ---- Orchestrator ----
    async def run(
        self,
        prompt_file_name: str,
        required_keys: set[str] | None = None,
        allowed_flags: set[str] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 256,
        **kwargs: Any,
    ) -> dict[str, Any]:

        # ---- Step 1: Build ----
        built = await self.build_messages(
            prompt_file_name=prompt_file_name,
            **kwargs,
        )
        if not built["state"]:
            return built

        # ---- Step 2: Generate ----
        generated = await self.generate_llm(
            messages=built["data"],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if not generated["state"]:
            return generated

        # ---- Step 3: Extract ----
        extracted = await self.extract_json(
            raw=generated["data"],
        )
        if not extracted["state"]:
            return extracted

        # ---- Step 4: Validate ----
        validated = self.validate_output(
            parsed=extracted["data"],
            required_keys=required_keys,
            allowed_flags=allowed_flags,
        )
        if not validated["state"]:
            return validated

        # ---- Final ----
        return {
            "state": True,
            "data": validated["data"],
        }