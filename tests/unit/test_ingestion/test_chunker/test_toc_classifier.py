import pytest
from langchain_core.documents import Document

from src.modules.ingestion.chunker.toc_classifier import TOCClassifier
from src.bootstrap.dependencies import get_chunker_toc_classifier

pytestmark = pytest.mark.unit


# ---- Fixture ----
@pytest.fixture
def toc_classifier() -> TOCClassifier:
    return get_chunker_toc_classifier()


# ---------------- has_toc_keywords ----------------

@pytest.mark.parametrize("text", [
    "Table of Contents",
    "This document contains contents",
    "Brief contents inside",
    "outline of the book",
])
def test_has_toc_keywords_positive(toc_classifier, text):
    assert toc_classifier.has_toc_keywords(text) is True


def test_has_toc_keywords_negative(toc_classifier):
    text = "This is just a normal document"
    assert toc_classifier.has_toc_keywords(text) is False


def test_has_toc_keywords_empty(toc_classifier):
    assert toc_classifier.has_toc_keywords("") is False


# ---------------- get_dots_density ----------------

def test_get_dots_density_basic(toc_classifier):
    text = "Chapter 1 ....\nChapter 2 ....\nChapter 3"
    result = toc_classifier.get_dots_density(text)

    assert result == 2 / 3


def test_get_dots_density_no_dots(toc_classifier):
    text = "Chapter 1\nChapter 2\nChapter 3"
    result = toc_classifier.get_dots_density(text)

    assert result == 0.0


def test_get_dots_density_empty(toc_classifier):
    assert toc_classifier.get_dots_density("") == 0.0


# ---------------- get_page_num_density ----------------

def test_get_page_num_density_basic(toc_classifier):
    text = "Chapter 1 1\nChapter 2 2\nChapter 3 text"
    result = toc_classifier.get_page_num_density(text)

    assert result == 2 / 3


def test_get_page_num_density_no_matches(toc_classifier):
    text = "Chapter one\nChapter two\nChapter three"
    result = toc_classifier.get_page_num_density(text)

    assert result == 0.0


def test_get_page_num_density_empty(toc_classifier):
    assert toc_classifier.get_page_num_density("") == 0.0


# ---------------- compute_toc_score ----------------

def test_compute_toc_score_with_keywords_only(toc_classifier):
    text = "Table of Contents\nIntro\nChapter 1"
    score = toc_classifier.compute_toc_score(text)

    assert 0.4 <= score <= 1.0


def test_compute_toc_score_with_dots_and_pages(toc_classifier):
    text = "Chapter 1 .... 1\nChapter 2 .... 2\nChapter 3 .... 3"
    score = toc_classifier.compute_toc_score(text)

    assert score > 0


def test_compute_toc_score_empty(toc_classifier):
    assert toc_classifier.compute_toc_score("") == 0.0


# ---------------- is_toc ----------------

def test_is_toc_positive(toc_classifier):
    text = "Table of Contents\nChapter 1 .... 1\nChapter 2 .... 2"
    result, score = toc_classifier.is_toc(text)

    assert result is True
    assert score >= toc_classifier.threshold


def test_is_toc_negative(toc_classifier):
    text = "This is a normal document without structure"
    result, score = toc_classifier.is_toc(text)

    assert result is False
    assert score < toc_classifier.threshold


# ---------------- enrich_metadata ----------------

def test_enrich_metadata_basic(toc_classifier):
    doc = Document(
        page_content="Table of Contents\nChapter 1 .... 1\nChapter 2 .... 2",
        metadata={"source": "test"}
    )

    new_metadata = toc_classifier.enrich_metadata(doc)

    assert "is_toc" in new_metadata
    assert "toc_score" in new_metadata
    assert "toc_threshold_used" in new_metadata

    assert isinstance(new_metadata["is_toc"], bool)
    assert isinstance(new_metadata["toc_score"], float)
    assert new_metadata["toc_threshold_used"] == toc_classifier.threshold


def test_enrich_metadata_preserves_original_metadata(toc_classifier):
    doc = Document(
        page_content="Normal text",
        metadata={"source": "file.pdf", "page": 1}
    )

    new_metadata = toc_classifier.enrich_metadata(doc)

    assert new_metadata["source"] == "file.pdf"
    assert new_metadata["page"] == 1