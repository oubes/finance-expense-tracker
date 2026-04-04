import pytest

from src.modules.ingestion.chunker.validator import TextValidator
from src.bootstrap.dependencies import get_chunker_validator

pytestmark = pytest.mark.unit


# ---- Fixture ----
@pytest.fixture
def validator() -> TextValidator:
    return get_chunker_validator()


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
def test_has_min_length(validator, text, min_length, expected):
    result = validator.has_min_length(text, min_length)
    assert result == expected


# ---------- has_enough_char_diversity ----------

def test_has_enough_char_diversity_true(validator):
    text = "abcde"
    assert validator.has_enough_char_diversity(text, 5) is True


def test_has_enough_char_diversity_false(validator):
    text = "aaaaa"
    assert validator.has_enough_char_diversity(text, 5) is False


def test_has_enough_char_diversity_default_param(validator):
    text = "abcdef"
    assert validator.has_enough_char_diversity(text) is True


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
def test_has_enough_words(validator, text, min_words, expected):
    assert validator.has_enough_words(text, min_words) == expected


# ---------- is_valid_text ----------

def test_is_valid_text_valid_case(validator):
    text = "abcde fghij klmno pqrst uvwxy zzzzz"
    assert validator.is_valid_text(text, min_length=20) is True


def test_is_valid_text_fails_min_length(validator):
    text = "abc def"
    assert validator.is_valid_text(text, min_length=20) is False


def test_is_valid_text_fails_char_diversity(validator):
    text = "aaaaaaaaaaaaaaaaaaaaa"
    assert validator.is_valid_text(text, min_length=10) is False


def test_is_valid_text_fails_word_count(validator):
    text = "abcde abcde abcde abcde"
    assert validator.is_valid_text(text, min_length=10) is False


def test_is_valid_text_all_conditions_default(validator):
    text = "abcde fghij klmno pqrst uvwxy gfsdf"
    assert validator.is_valid_text(text) is True