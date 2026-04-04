import pytest

from src.bootstrap.dependencies import get_chunk_scorer

pytestmark = pytest.mark.unit


# ---- Fixture ----
@pytest.fixture
def scorer():
    return get_chunk_scorer()


# ---------------- tokenize ----------------

def test_tokenize_basic(scorer):
    text = "Hello world 123!"
    tokens = scorer.tokenize(text)

    assert "hello" in tokens
    assert "world" in tokens
    assert "123" in tokens


# ---------------- length score ----------------

def test_length_score_bounds(scorer):
    text = "a" * 1000
    score = scorer.compute_length_score(text)

    assert 0.0 <= score <= 1.0


# ---------------- sentence count ----------------

def test_sentence_count_basic(scorer):
    text = "Hello. World! Test?"
    count = scorer.compute_sentence_count(text)

    assert count == 3


def test_sentence_count_empty(scorer):
    assert scorer.compute_sentence_count("") == 0


# ---------------- sentence score ----------------

def test_sentence_score_normalization(scorer):
    score = scorer.compute_sentence_score(5)

    assert 0.0 <= score <= 1.0


# ---------------- repetition ratio ----------------

def test_repetition_ratio_all_unique(scorer):
    words = ["a", "b", "c"]
    ratio = scorer.compute_repetition_ratio(len(words), len(set(words)))

    assert ratio == 0.0


def test_repetition_ratio_with_duplicates(scorer):
    words = ["a", "a", "b"]
    ratio = scorer.compute_repetition_ratio(len(words), len(set(words)))

    assert ratio > 0


# ---------------- alpha ratio ----------------

def test_alpha_ratio(scorer):
    text = "abc123!!!"
    ratio = scorer.compute_alpha_ratio(text)

    assert 0.0 < ratio < 1.0


def test_alpha_ratio_empty(scorer):
    assert scorer.compute_alpha_ratio("") == 0.0


# ---------------- domain vocab ratio ----------------

def test_domain_vocab_ratio_basic(scorer):
    words = ["income", "expense", "random"]
    ratio = scorer.compute_domain_vocab_ratio(words)

    assert 0.0 < ratio < 1.0


# ---------------- combine scores ----------------

def test_combine_scores(scorer):
    result = scorer.combine_scores(0.5, 0.5)

    assert 0.0 <= result <= 1.0


# ---------------- squash (sigmoid) ----------------

def test_squash_bounds(scorer):
    val = scorer.squash(0.5)

    assert 0.0 < val < 1.0


# ---------------- score_chunk ----------------

def test_score_chunk_simple_text(scorer):
    text = "This is a simple sentence."

    score = scorer.score_chunk(text)

    assert 0.0 <= score <= 1.0


def test_score_chunk_finance_domain_boost(scorer):
    text = "income investment budget money financial assets"

    score = scorer.score_chunk(text)

    assert 0.0 <= score <= 1.0


def test_score_chunk_repetition_penalty(scorer):
    text = "word word word word word"

    score = scorer.score_chunk(text)

    assert 0.0 <= score <= 1.0


def test_score_chunk_with_raw_text(scorer):
    text = "short"
    raw_text = "This is a longer raw text. It has multiple sentences. And structure."

    score = scorer.score_chunk(text, raw_text=raw_text)

    assert 0.0 <= score <= 1.0