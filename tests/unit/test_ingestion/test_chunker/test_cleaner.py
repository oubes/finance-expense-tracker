import pytest

from src.modules.ingestion.chunker.cleaner_pre import PreTextCleaner
from src.bootstrap.dependencies import get_chunker_pre_cleaner

pytestmark = pytest.mark.unit


# ---- Fixture ----
@pytest.fixture
def cleaner() -> PreTextCleaner:
    return get_chunker_pre_cleaner()


# ---------------- normalize_text ----------------

def test_normalize_text_lowercase_and_accents(cleaner: PreTextCleaner):
    assert cleaner.normalize_text("Café ÀBC", lowercase=True, remove_accents=True) == "cafe abc"


def test_normalize_text_no_lowercase(cleaner: PreTextCleaner):
    assert cleaner.normalize_text("Café ABC", lowercase=False, remove_accents=True) == "Cafe ABC"


def test_normalize_text_no_accents(cleaner: PreTextCleaner):
    assert cleaner.normalize_text("Café ABC", lowercase=True, remove_accents=False) == "café abc"


# ---------------- normalize_whitespace ----------------

def test_normalize_whitespace_basic(cleaner: PreTextCleaner):
    assert cleaner.normalize_whitespace("hello    world   test") == "hello world test"


def test_normalize_whitespace_with_newlines_and_tabs(cleaner: PreTextCleaner):
    assert cleaner.normalize_whitespace("hello\t\tworld\n\ntest") == "hello world test"


# ---------------- replace_ampersand ----------------

def test_replace_ampersand_basic(cleaner: PreTextCleaner):
    assert cleaner.replace_ampersand("apple & banana") == "apple and banana"


def test_replace_ampersand_with_spaces(cleaner: PreTextCleaner):
    assert cleaner.replace_ampersand("apple   &    banana") == "apple and banana"


def test_replace_ampersand_inside_word(cleaner: PreTextCleaner):
    assert cleaner.replace_ampersand("rock&roll") == "rock and roll"


# ---------------- remove_special_chars ----------------

def test_remove_special_chars_basic(cleaner: PreTextCleaner):
    assert cleaner.remove_special_chars("hello@world!") == "hello@world!"


def test_remove_special_chars_removes_unwanted(cleaner: PreTextCleaner):
    assert cleaner.remove_special_chars("hello#world$%^") == "helloworld$%"


def test_remove_special_chars_keeps_allowed(cleaner: PreTextCleaner):
    assert cleaner.remove_special_chars("hi, how are you? (test) - done.") == "hi, how are you? (test) - done."


# ---------------- clean_text pipeline ----------------

def test_clean_text_full_pipeline(cleaner: PreTextCleaner):
    assert cleaner.clean("  Café   &   MATH!!!  ") == "cafe and math!!!"


def test_clean_text_no_lowercase(cleaner: PreTextCleaner):
    assert cleaner.clean("  Café & MATH!!!  ", lowercase=False, remove_accents=True) == "Cafe and MATH!!!"


def test_clean_text_no_accents(cleaner: PreTextCleaner):
    assert cleaner.clean("  Café & Math!!!  ", lowercase=True, remove_accents=False) == "café and math!!!"

def test_clean_text_multiple_spaces_and_symbols(cleaner: PreTextCleaner):
    assert cleaner.clean("Hello   &   World   ### !!!") == "hello and world !!!"