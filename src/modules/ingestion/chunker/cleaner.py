import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = " ".join(text.split())

    # remove repeated noisy characters
    text = re.sub(r"(.)\1{3,}", r"\1", text)

    return text