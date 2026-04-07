# ---- Imports ----
import json
import re
from typing import Any


class LLMJsonExtractor:

    # ---- Extract One ----
    def extract_one(self, raw_data: str) -> dict[str, Any]:
        try:
            text = raw_data.strip()

            # ---- Handle markdown code blocks ----
            if text.startswith("```"):
                text = re.sub(r"\n```$", "", text).strip()

            # ---- Try strict JSON parse first ----
            try:
                parsed = json.loads(text)

                if isinstance(parsed, dict):
                    # ---- Preserve raw values without destroying structure ----
                    normalized = {
                        k: (v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))
                        for k, v in parsed.items()
                    }

                    return {
                        "state": True,
                        "data": normalized
                    }

            except Exception:
                pass

            # ---- Fallback manual extraction ----
            if text.startswith("{"):
                text = text[1:].strip()
            if text.endswith("}"):
                text = text[:-1].strip()

            extracted_dict: dict[str, str] = {}

            key_pattern = re.compile(r'"(\w+)"\s*:\s*')
            pos = 0

            while pos < len(text):
                match = key_pattern.search(text, pos)
                if not match:
                    break

                key = match.group(1)
                value_start = match.end()

                bracket_count = 0
                brace_count = 0
                in_quotes = False
                escape = False
                value_end = len(text)

                for i in range(value_start, len(text)):
                    char = text[i]

                    if escape:
                        escape = False
                        continue
                    if char == '\\':
                        escape = True
                        continue
                    if char == '"':
                        in_quotes = not in_quotes
                        continue

                    if not in_quotes:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                        elif char == '[':
                            bracket_count += 1
                        elif char == ']':
                            bracket_count -= 1
                        elif char == ',' and brace_count <= 0 and bracket_count <= 0:
                            value_end = i
                            break

                val = text[value_start:value_end].strip()

                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]

                extracted_dict[key] = val
                pos = value_end + 1

            if not extracted_dict:
                return {"state": False, "data": None}

            return {"state": True, "data": extracted_dict}

        except Exception:
            return {"state": False, "data": None}

    # ---- Extract Batch ----
    def extract_batch(self, raw_data_list: list[str]) -> list[dict[str, Any]]:
        return [self.extract_one(raw) for raw in raw_data_list]