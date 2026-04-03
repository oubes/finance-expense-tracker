def has_min_length(text: str, min_length: int) -> bool:
    return bool(text) and len(text) >= min_length


def has_enough_char_diversity(text: str, min_unique_chars: int = 5) -> bool:
    return len(set(text)) >= min_unique_chars


def has_enough_words(text: str, min_words: int = 5) -> bool:
    return len(text.split()) > min_words


def is_valid_text(text: str, min_length: int = 20) -> bool:

    if not has_min_length(text, min_length):
        return False

    if not has_enough_char_diversity(text):
        return False

    if not has_enough_words(text):
        return False

    return True