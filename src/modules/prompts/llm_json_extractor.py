# ---- Imports ----
import json
import logging
from typing import Any


# ---- Logger ----
logger = logging.getLogger(__name__)


class LLMJsonExtractor:
    # ---- Extract One ----
    def extract_one(self, raw_output: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw_output)
        except Exception:
            return {"state": False, "data": None}

        if not isinstance(parsed, dict):
            return {"state": False, "data": None}

        return {"state": True, "data": parsed}

    # ---- Extract Batch ----
    def extract_batch(self, raw_outputs: list[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []

        for raw in raw_outputs:
            results.append(self.extract_one(raw))

        return results