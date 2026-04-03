import re
import unicodedata


def normalize_text(text: str, *, lowercase: bool = True, remove_accents: bool = False) -> str:
    text = unicodedata.normalize("NFKC", text)

    if remove_accents:
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))

    if lowercase:
        text = text.lower()

    return text

def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def replace_ampersand(text: str) -> str:
    # Replace standalone & with "and"
    return re.sub(r"\s*&\s*", " and ", text)


def remove_special_chars(text: str) -> str:
    return re.sub(r"[^\w\s.,;:!?()\-@$%]", "", text)


def clean_text(text: str, *, lowercase: bool = True, remove_accents: bool = False) -> str:
    text = normalize_text(text, lowercase=lowercase, remove_accents=remove_accents)

    text = normalize_whitespace(text)
    text = replace_ampersand(text)

    text = remove_special_chars(text)

    text = normalize_whitespace(text)

    return text