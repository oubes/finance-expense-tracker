# ---- Imports ----
import re
import orjson
import asyncio
from typing import Any


class LLMJsonExtractor:

    # ---- Precompiled ----
    _codeblock_pattern = re.compile(r"^```(?:json)?|```$", re.MULTILINE)
    _key_pattern = re.compile(r'"(\w+)"\s*:\s*')

    # ---- Clean ----
    def _clean(self, text: str) -> str:
        return self._codeblock_pattern.sub("", text).strip()

    # ---- Normalize ----
    def _normalize(self, data: dict) -> dict[str, str]:
        return {
            k: (v if isinstance(v, str) else orjson.dumps(v).decode())
            for k, v in data.items()
        }

    # ---- Parse ----
    def _parse(self, text: str) -> dict[str, Any]:
        parsed = orjson.loads(text)
        return self._normalize(parsed)

    # ---- Fallback ----
    def _fallback(self, text: str) -> dict[str, str]:
        extracted: dict[str, str] = {}
        for m in self._key_pattern.finditer(text):
            key = m.group(1)
            start = m.end()
            end = text.find(",", start)
            if end == -1:
                end = len(text)
            val = text[start:end].strip().strip('"')
            extracted[key] = val
        return extracted

    # ---- Sync Core ----
    def _extract_sync(self, raw_data: str) -> dict[str, Any]:
        try:
            text = self._clean(raw_data)

            try:
                parsed = self._parse(text)
                return {"state": True, "data": parsed}
            except Exception:
                pass

            fallback = self._fallback(text)
            if fallback:
                return {"state": True, "data": fallback}

            return {"state": False, "data": None}

        except Exception:
            return {"state": False, "data": None}

    # ---- Async Wrapper ----
    async def extract_one(self, raw_data: str) -> dict[str, Any]:
        return await asyncio.to_thread(self._extract_sync, raw_data)

    # ---- Async Batch ----
    async def extract_batch(self, raw_data_list: list[str]) -> list[dict[str, Any]]:
        return await asyncio.gather(
            *[self.extract_one(item) for item in raw_data_list]
        )