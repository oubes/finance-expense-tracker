# ---- Imports ----
import json
from typing import Any


class LLMJsonValidator:
    # ---- Constructor ----
    def __init__(self, required_keys: set[str], allowed_flags: set[str] | None = None):
        self.required_keys = required_keys
        self.allowed_flags = allowed_flags

    # ---- Validate One ----
    def validate_one(self, raw_output: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw_output)
        except Exception:
            return {"state": False, "data": None}

        if not isinstance(parsed, dict):
            return {"state": False, "data": None}

        if self.required_keys - parsed.keys():
            return {"state": False, "data": None}

        if self.allowed_flags is not None and "flag" in parsed:
            if parsed["flag"] not in self.allowed_flags:
                return {"state": False, "data": None}

        return {"state": True, "data": parsed}

    # ---- Validate Batch ----
    def validate_batch(self, raw_outputs: list[str]) -> list[dict[str, Any]]:
        return [self.validate_one(raw) for raw in raw_outputs]