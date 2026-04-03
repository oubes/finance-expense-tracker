def is_valid_text(text: str, min_length: int) -> bool:
    if not text or len(text) < min_length:
        return False

    if len(set(text)) < 5:
        return False

    if len(text.split()) <= 5:
        return False

    return True