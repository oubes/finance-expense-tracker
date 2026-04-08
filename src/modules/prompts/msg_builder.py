# ---- Imports ----
from typing import Any
import re
import asyncio
from src.modules.prompts.prompt_loader import PromptLoader
from src.modules.prompts.prompt_registry import PromptRegistry


class MsgBuilder:
    # ---- Constructor ----
    def __init__(
        self,
        prompt_loader: PromptLoader,
        registry: PromptRegistry,
    ):
        self.prompt_loader = prompt_loader
        self.registry = registry

    # ---- Safe Dict ----
    class _SafeDict(dict):
        def __missing__(self, key: str) -> str:
            return ""

    # ---- Extract Flags ----
    def _extract_flags(self, prompt_sections: dict[str, str]) -> list[str]:
        flags: set[str] = set()
        pattern = re.compile(r"[A-Z0-9_]+_FLAG")

        for section_text in prompt_sections.values():
            matches = pattern.findall(section_text)
            for match in matches:
                clean = match.strip().strip("<>").strip('"').strip()
                if clean.endswith("_FLAG"):
                    flags.add(clean)

        return sorted(flags)

    # ---- Build Async ----
    async def build_async(
        self,
        prompt_file_name: str,
        **kwargs: Any,
    ) -> dict[str, Any]:

        # ---- Resolve Prompt File ----
        try:
            file_path = self.registry.get(prompt_file_name)

            # Run blocking I/O in thread
            prompt_sections = await asyncio.to_thread(
                self.prompt_loader.load,
                file_path
            )

        except Exception:
            return {"state": False, "data": None, "flags": []}

        # ---- Extract Sections ----
        system_prompt = prompt_sections.get("system")
        user_prompt = prompt_sections.get("user", "")

        # ---- Extract Flags ----
        flags = self._extract_flags(prompt_sections)

        # ---- Normalize Inputs ----
        kwargs = {k: ("" if v is None else v) for k, v in kwargs.items()}

        # ---- Format User Prompt ----
        try:
            user_content = user_prompt.format_map(self._SafeDict(kwargs))
        except Exception:
            return {"state": False, "data": None, "flags": flags}

        # ---- Construct Messages ----
        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        messages.append({
            "role": "user",
            "content": user_content
        })

        return {
            "state": True,
            "data": messages,
            "flags": flags
        }

    # ---- Batch Build Async ----
    async def build_batch_async(
        self,
        prompt_file_name: str,
        inputs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        tasks = [
            self.build_async(prompt_file_name=prompt_file_name, **kwargs)
            for kwargs in inputs
        ]

        return await asyncio.gather(*tasks)