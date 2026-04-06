import json
import re
from typing import Any


class LLMJsonValidator:
    # ---- Repair Truncated JSON ----
    def _repair_json_string(self, raw_str: str) -> str:
        """Attempt to close unbalanced braces in truncated JSON strings."""
        raw_str = raw_str.strip()

        # Count unmatched opening braces
        opened_braces = raw_str.count('{') - raw_str.count('}')

        if opened_braces > 0:
            raw_str += '}' * opened_braces

        # Remove trailing commas before closing brackets/braces
        raw_str = re.sub(r',\s*([\]}])', r'\1', raw_str)

        return raw_str

    # ---- Convert Values to Strings Safely ----
    def _to_str(self, value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, str):
            return value

        try:
            # Convert dict/list to compact JSON string
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)

    # ---- Normalize Dictionary Structure ----
    def _normalize_dict(self, data: dict[str, Any]) -> dict[str, str]:
        return {str(k): self._to_str(v) for k, v in data.items()}

    # ---- Validate Single Item ----
    def validate_one(
        self,
        parsed: dict[str, Any],
        required_keys: set[str] | None = None,
        allowed_flags: set[str] | None = None,
        lenient_mode: bool = True  # Allow partially valid / truncated data
    ) -> dict[str, Any]:

        # ---- Unwrap Extractor Output ----
        if isinstance(parsed, dict) and "state" in parsed and "data" in parsed:
            if not parsed["state"] or parsed["data"] is None:
                return {"state": False, "data": None}
            parsed = parsed["data"]

        # ---- Ensure Input is Dict ----
        if not isinstance(parsed, dict):
            return {"state": False, "data": None}

        # ---- Required Keys Check ----
        if required_keys:
            missing_keys = required_keys - set(parsed.keys())

            # In lenient mode, accept if summary exists
            if missing_keys:
                if not ("summary" in parsed and lenient_mode):
                    return {"state": False, "data": None}

        # ---- Flag Validation ----
        if allowed_flags and "flag" in parsed:
            if parsed["flag"] not in allowed_flags:
                return {"state": False, "data": None}
        elif allowed_flags and "flag" not in parsed and not lenient_mode:
            return {"state": False, "data": None}

        # ---- Normalize All Values to Strings ----
        normalized_data = self._normalize_dict(parsed)

        return {"state": True, "data": normalized_data}

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