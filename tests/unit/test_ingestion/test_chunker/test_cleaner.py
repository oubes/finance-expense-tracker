import pytest

from src.modules.ingestion.chunker.cleaner import TextCleaner
from src.bootstrap.dependencies import get_chunker_cleaner

pytestmark = pytest.mark.unit


# ---- Fixture ----
@pytest.fixture
def cleaner() -> TextCleaner:
    return get_chunker_cleaner()


# ---------------- normalize_text ----------------

def test_normalize_text_lowercase_and_accents(cleaner: TextCleaner):
    assert cleaner.normalize_text("Café ÀBC", lowercase=True, remove_accents=True) == "cafe abc"


def test_normalize_text_no_lowercase(cleaner: TextCleaner):
    assert cleaner.normalize_text("Café ABC", lowercase=False, remove_accents=True) == "Cafe ABC"


def test_normalize_text_no_accents(cleaner: TextCleaner):
    assert cleaner.normalize_text("Café ABC", lowercase=True, remove_accents=False) == "café abc"


# ---------------- normalize_whitespace ----------------

def test_normalize_whitespace_basic(cleaner: TextCleaner):
    assert cleaner.normalize_whitespace("hello    world   test") == "hello world test"


def test_normalize_whitespace_with_newlines_and_tabs(cleaner: TextCleaner):
    assert cleaner.normalize_whitespace("hello\t\tworld\n\ntest") == "hello world test"


# ---------------- replace_ampersand ----------------

def test_replace_ampersand_basic(cleaner: TextCleaner):
    assert cleaner.replace_ampersand("apple & banana") == "apple and banana"


def test_replace_ampersand_with_spaces(cleaner: TextCleaner):
    assert cleaner.replace_ampersand("apple   &    banana") == "apple and banana"


def test_replace_ampersand_inside_word(cleaner: TextCleaner):
    assert cleaner.replace_ampersand("rock&roll") == "rock and roll"


# ---------------- remove_special_chars ----------------

def test_remove_special_chars_basic(cleaner: TextCleaner):
    assert cleaner.remove_special_chars("hello@world!") == "hello@world!"


def test_remove_special_chars_removes_unwanted(cleaner: TextCleaner):
    assert cleaner.remove_special_chars("hello#world$%^") == "helloworld$%"


def test_remove_special_chars_keeps_allowed(cleaner: TextCleaner):
    assert cleaner.remove_special_chars("hi, how are you? (test) - done.") == "hi, how are you? (test) - done."


# ---------------- clean_text pipeline ----------------

def test_clean_text_full_pipeline(cleaner: TextCleaner):
    assert cleaner.clean_text("  Café   &   MATH!!!  ") == "cafe and math!!!"


def test_clean_text_no_lowercase(cleaner: TextCleaner):
    assert cleaner.clean_text("  Café & MATH!!!  ", lowercase=False, remove_accents=True) == "Cafe and MATH!!!"


def test_clean_text_no_accents(cleaner: TextCleaner):
    assert cleaner.clean_text("  Café & Math!!!  ", lowercase=True, remove_accents=False) == "café and math!!!"


def test_clean_text_multiple_spaces_and_symbols(cleaner: TextCleaner):
    assert cleaner.clean_text("Hello   &   World   ### !!!") == "hello and world !!!"