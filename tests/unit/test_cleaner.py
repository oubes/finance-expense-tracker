import pytest

from src.modules.ingestion.chunker.cleaner import (
    normalize_text,
    normalize_whitespace,
    replace_ampersand,
    remove_special_chars,
    clean_text,
)

pytestmark = pytest.mark.chunk_cleaner

# ---------------- normalize_text ----------------

def test_normalize_text_lowercase_and_accents():
    text = "Café ÀBC"
    result = normalize_text(text, lowercase=True, remove_accents=True)

    assert result == "cafe abc"


def test_normalize_text_no_lowercase():
    text = "Café ABC"
    result = normalize_text(text, lowercase=False, remove_accents=True)

    assert result == "Cafe ABC"


def test_normalize_text_no_accents():
    text = "Café ABC"
    result = normalize_text(text, lowercase=True, remove_accents=False)

    assert result == "café abc"


# ---------------- normalize_whitespace ----------------

def test_normalize_whitespace_basic():
    text = "hello    world   test"
    result = normalize_whitespace(text)

    assert result == "hello world test"


def test_normalize_whitespace_with_newlines_and_tabs():
    text = "hello\t\tworld\n\ntest"
    result = normalize_whitespace(text)

    assert result == "hello world test"


# ---------------- replace_ampersand ----------------

def test_replace_ampersand_basic():
    text = "apple & banana"
    result = replace_ampersand(text)

    assert result == "apple and banana"


def test_replace_ampersand_with_spaces():
    text = "apple   &    banana"
    result = replace_ampersand(text)

    assert result == "apple and banana"


def test_replace_ampersand_inside_word_should_not_replace():
    text = "rock&roll"
    result = replace_ampersand(text)

    assert result == "rock and roll"


# ---------------- remove_special_chars ----------------

def test_remove_special_chars_basic():
    text = "hello@world!"
    result = remove_special_chars(text)

    assert result == "hello@world!"


def test_remove_special_chars_removes_unwanted():
    text = "hello#world$%^"
    result = remove_special_chars(text)

    assert result == "helloworld$%"


def test_remove_special_chars_keeps_allowed_punctuation():
    text = "hi, how are you? (test) - done."
    result = remove_special_chars(text)

    assert result == "hi, how are you? (test) - done."


# ---------------- clean_text pipeline ----------------

def test_clean_text_full_pipeline():
    text = "  Café   &   MATH!!!  "
    result = clean_text(text, lowercase=True, remove_accents=True)

    assert result == "cafe and math!!!"


def test_clean_text_no_lowercase():
    text = "  Café & MATH!!!  "
    result = clean_text(text, lowercase=False, remove_accents=True)

    assert result == "Cafe and MATH!!!"


def test_clean_text_no_accents():
    text = "  Café & Math!!!  "
    result = clean_text(text, lowercase=True, remove_accents=False)

    assert result == "café and math!!!"


def test_clean_text_multiple_spaces_and_symbols():
    text = "Hello   &   World   ### !!!"
    result = clean_text(text)

    assert result == "hello and world !!!"