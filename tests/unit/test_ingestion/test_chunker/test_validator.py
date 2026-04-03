import pytest

from src.modules.ingestion.chunker.validator import (
    has_min_length,
    has_enough_char_diversity,
    has_enough_words,
    is_valid_text,
)

pytestmark = pytest.mark.chunk_validator

# ---------- has_min_length ----------

@pytest.mark.parametrize(
    "text,min_length,expected",
    [
        ("hello", 3, True),
        ("hello", 5, True),
        ("hello", 6, False),
        ("", 1, False),
        (None, 1, False),
    ],
)
def test_has_min_length(text, min_length, expected):
    result = has_min_length(text, min_length)
    assert result == expected


# ---------- has_enough_char_diversity ----------

def test_has_enough_char_diversity_true():
    text = "abcde"
    assert has_enough_char_diversity(text, 5) is True


def test_has_enough_char_diversity_false():
    text = "aaaaa"
    assert has_enough_char_diversity(text, 5) is False


def test_has_enough_char_diversity_default_param():
    text = "abcdef"
    assert has_enough_char_diversity(text) is True


# ---------- has_enough_words ----------

@pytest.mark.parametrize(
    "text,min_words,expected",
    [
        ("one two three four five", 5, False),
        ("one two three four five six", 5, True),
        ("a b c d e f", 5, True),
        ("a b c d", 3, True),
    ],
)
def test_has_enough_words(text, min_words, expected):
    assert has_enough_words(text, min_words) == expected


# ---------- is_valid_text ----------

def test_is_valid_text_valid_case():
    text = "abcde fghij klmno pqrst uvwxy zzzzz"
    assert is_valid_text(text, min_length=20) is True


def test_is_valid_text_fails_min_length():
    text = "abc def"
    assert is_valid_text(text, min_length=20) is False


def test_is_valid_text_fails_char_diversity():
    text = "aaaaaaaaaaaaaaaaaaaaa"
    assert is_valid_text(text, min_length=10) is False


def test_is_valid_text_fails_word_count():
    text = "abcde abcde abcde abcde"
    assert is_valid_text(text, min_length=10) is False


def test_is_valid_text_all_conditions_default():
    text = "abcde fghij klmno pqrst uvwxy gfsdf"
    assert is_valid_text(text) is True