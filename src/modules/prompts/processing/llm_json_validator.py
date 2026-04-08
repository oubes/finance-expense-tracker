# ---- Imports ----
import re
import orjson
from typing import Any


class LLMJsonValidator:

    # ---- Precompiled Patterns ----
    _trailing_comma_pattern = re.compile(r',\s*([\]}])')

    # ---- Repair JSON ----
    def _repair_json_string(self, raw_str: str) -> str:
        raw_str = raw_str.strip()

        diff = raw_str.count('{') - raw_str.count('}')
        if diff > 0:
            raw_str += '}' * diff

        return self._trailing_comma_pattern.sub(r'\1', raw_str)

    # ---- Convert Value to String ----
    def _to_str(self, value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, str):
            return value

        try:
            return orjson.dumps(value).decode()
        except Exception:
            return str(value)

    # ---- Normalize Dictionary ----
    def _normalize_dict(self, data: dict[str, Any]) -> dict[str, str]:
        return {
            k if isinstance(k, str) else str(k): self._to_str(v)
            for k, v in data.items()
        }

    # ---- Validate One ----
    def validate_one(
        self,
        parsed: dict[str, Any],
        required_keys: set[str] | None = None,
        allowed_flags: set[str] | None = None,
        lenient_mode: bool = True,
    ) -> dict[str, Any]:

        if isinstance(parsed, dict) and "state" in parsed:
            if not parsed.get("state") or parsed.get("data") is None:
                return {"state": False, "data": None}
            parsed = parsed["data"]

        if not isinstance(parsed, dict):
            return {"state": False, "data": None}

        if required_keys:
            missing = [k for k in required_keys if k not in parsed]
            if missing and not (lenient_mode and "summary" in parsed):
                return {"state": False, "data": None}

        if allowed_flags:
            flag = parsed.get("flag")
            if flag is None:
                if not lenient_mode:
                    return {"state": False, "data": None}
            elif flag not in allowed_flags:
                return {"state": False, "data": None}

        parsed.setdefault("title", "")

        return {
            "state": True,
            "data": self._normalize_dict(parsed),
        }

    # ---- Validate Batch ----
    def validate_batch(
        self,
        parsed_outputs: list[dict[str, Any]],
        required_keys: set[str] | None = None,
        allowed_flags: set[str] | None = None,
    ) -> list[dict[str, Any]]:

        return [
            self.validate_one(
                item,
                required_keys=required_keys,
                allowed_flags=allowed_flags,
            )
            for item in parsed_outputs
        ]