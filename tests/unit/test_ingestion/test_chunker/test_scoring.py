import pytest

from src.modules.ingestion.chunker.scoring import (
    score_chunk,
    _tokenize,
    _compute_length_score,
    _compute_sentence_count,
    _compute_sentence_score,
    _compute_repetition_ratio,
    _compute_alpha_ratio,
    _compute_domain_vocab_ratio,
    _combine_scores,
    _squash,
)

pytestmark = pytest.mark.chunk_scoring

# ---------------- tokenize ----------------

def test_tokenize_basic():
    text = "Hello world 123!"
    tokens = _tokenize(text)

    assert "hello" in tokens
    assert "world" in tokens
    assert "123" in tokens


# ---------------- length score ----------------

def test_length_score_bounds():
    text = "a" * 1000
    score = _compute_length_score(text)

    assert 0.0 <= score <= 1.0


# ---------------- sentence count ----------------

def test_sentence_count_basic():
    text = "Hello. World! Test?"
    count = _compute_sentence_count(text)

    assert count == 3


def test_sentence_count_empty():
    assert _compute_sentence_count("") == 0


# ---------------- sentence score ----------------

def test_sentence_score_normalization():
    score = _compute_sentence_score(5)

    assert 0.0 <= score <= 1.0


# ---------------- repetition ratio ----------------

def test_repetition_ratio_all_unique():
    words = ["a", "b", "c"]
    ratio = _compute_repetition_ratio(len(words), len(set(words)))

    assert ratio == 0.0


def test_repetition_ratio_with_duplicates():
    words = ["a", "a", "b"]
    ratio = _compute_repetition_ratio(len(words), len(set(words)))

    assert ratio > 0


# ---------------- alpha ratio ----------------

def test_alpha_ratio():
    text = "abc123!!!"
    ratio = _compute_alpha_ratio(text)

    assert 0.0 < ratio < 1.0


def test_alpha_ratio_empty():
    assert _compute_alpha_ratio("") == 0.0


# ---------------- domain vocab ratio ----------------

def test_domain_vocab_ratio_basic():
    words = ["income", "expense", "random"]
    ratio = _compute_domain_vocab_ratio(words)

    assert 0.0 < ratio < 1.0


# ---------------- combine scores ----------------

def test_combine_scores():
    result = _combine_scores(0.5, 0.5)

    assert 0.0 <= result <= 1.0


# ---------------- squash (sigmoid) ----------------

def test_squash_bounds():
    val = _squash(0.5)

    assert 0.0 < val < 1.0


# ---------------- score_chunk ----------------

def test_score_chunk_simple_text():
    text = "This is a simple sentence."

    score = score_chunk(text)

    assert 0.0 <= score <= 1.0


def test_score_chunk_finance_domain_boost():
    text = "income investment budget money financial assets"

    score = score_chunk(text)

    assert 0.0 <= score <= 1.0


def test_score_chunk_repetition_penalty():
    text = "word word word word word"

    score = score_chunk(text)

    assert 0.0 <= score <= 1.0


def test_score_chunk_with_raw_text():
    text = "short"
    raw_text = "This is a longer raw text. It has multiple sentences. And structure."

    score = score_chunk(text, raw_text=raw_text)

    assert 0.0 <= score <= 1.0