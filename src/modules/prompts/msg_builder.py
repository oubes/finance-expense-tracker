# ---- Imports ----
from typing import Any
from src.modules.prompts.prompt_loader import PromptLoader
from src.modules.prompts.prompt_registry import PromptRegistry
from src.modules.prompts.llm_json_validator import LLMJsonValidator
from src.modules.prompts.llm_json_extractor import LLMJsonExtractor


# ---- Msg Builder ----
class MsgBuilder:
    # ---- Constructor ----
    def __init__(
        self,
        prompt_loader: PromptLoader,
        registry: PromptRegistry,
        validator: LLMJsonValidator,
        extractor: LLMJsonExtractor
    ):
        self.prompt_loader = prompt_loader
        self.registry = registry
        self.validator = validator
        self.extractor = extractor

    # ---- Safe Dict ----
    class _SafeDict(dict):
        def __missing__(self, key: str) -> str:
            return ""

    # ---- Build Messages ----
    def build(
        self,
        prompt_file_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:

        try:
            file_path = self.registry.get(prompt_file_name)
            prompt_sections = self.prompt_loader.load(file_path)
        except Exception:
            return {"state": False, "data": None}

        system_prompt = prompt_sections.get("system")
        user_prompt = prompt_sections.get("user", "")

        kwargs = {k: ("" if v is None else v) for k, v in kwargs.items()}

        try:
            user_content = user_prompt.format_map(self._SafeDict(kwargs))
        except Exception:
            return {"state": False, "data": None}

        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": user_content})

        return {"state": True, "data": messages}

    # ---- Batch Build ----
    def build_batch(
        self,
        prompt_file_name: str,
        inputs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        results: list[dict[str, Any]] = []

        for kwargs in inputs:
            results.append(self.build(prompt_file_name=prompt_file_name, **kwargs))

        return results

    # ---- Post Process One ----
    def post_process_one(self, raw_output: str) -> dict[str, Any]:
        if not self.validator or not self.extractor:
            return {"state": False, "data": None}

        extract_res = self.extractor.extract_one(raw_output)
        if not extract_res["state"]:
            return {"state": False, "data": None}

        validate_res = self.validator.validate_one(raw_output)
        if not validate_res["state"]:
            return {"state": False, "data": None}

        return {"state": True, "data": validate_res["data"]}

    # ---- Post Process Batch ----
    def post_process_batch(self, raw_outputs: list[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        for raw in raw_outputs:
            results.append(self.post_process_one(raw))

        return results