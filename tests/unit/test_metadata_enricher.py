import pytest
from langchain_core.documents import Document

from src.modules.ingestion.chunker.metadata_enricher import (
    has_toc_keywords,
    get_dots_density,
    get_page_num_density,
    compute_toc_score,
    is_toc,
    enrich_metadata,
    TOC_THRESHOLD,
)


pytestmark = pytest.mark.chunk_metadata_enricher


# ---------------- has_toc_keywords ----------------

@pytest.mark.parametrize("text", [
    "Table of Contents",
    "This document contains contents",
    "Brief contents inside",
    "outline of the book",
])
def test_has_toc_keywords_positive(text):
    assert has_toc_keywords(text) is True


def test_has_toc_keywords_negative():
    text = "This is just a normal document"
    assert has_toc_keywords(text) is False


def test_has_toc_keywords_empty():
    assert has_toc_keywords("") is False


# ---------------- get_dots_density ----------------

def test_get_dots_density_basic():
    text = "Chapter 1 ....\nChapter 2 ....\nChapter 3"
    result = get_dots_density(text)

    assert result == 2 / 3


def test_get_dots_density_no_dots():
    text = "Chapter 1\nChapter 2\nChapter 3"
    result = get_dots_density(text)

    assert result == 0.0


def test_get_dots_density_empty():
    assert get_dots_density("") == 0.0


# ---------------- get_page_num_density ----------------

def test_get_page_num_density_basic():
    text = "Chapter 1 1\nChapter 2 2\nChapter 3 text"
    result = get_page_num_density(text)

    assert result == 2 / 3


def test_get_page_num_density_no_matches():
    text = "Chapter one\nChapter two\nChapter three"
    result = get_page_num_density(text)

    assert result == 0.0


def test_get_page_num_density_empty():
    assert get_page_num_density("") == 0.0


# ---------------- compute_toc_score ----------------

def test_compute_toc_score_with_keywords_only():
    text = "Table of Contents\nIntro\nChapter 1"
    score = compute_toc_score(text)

    assert 0.4 <= score <= 1.0


def test_compute_toc_score_with_dots_and_pages():
    text = "Chapter 1 .... 1\nChapter 2 .... 2\nChapter 3 .... 3"
    score = compute_toc_score(text)

    assert score > 0


def test_compute_toc_score_empty():
    assert compute_toc_score("") == 0.0


# ---------------- is_toc ----------------

def test_is_toc_positive():
    text = "Table of Contents\nChapter 1 .... 1\nChapter 2 .... 2"
    result, score = is_toc(text)

    assert result is True
    assert score >= TOC_THRESHOLD


def test_is_toc_negative():
    text = "This is a normal document without structure"
    result, score = is_toc(text)

    assert result is False
    assert score < TOC_THRESHOLD


# ---------------- enrich_metadata ----------------

def test_enrich_metadata_basic():
    doc = Document(
        page_content="Table of Contents\nChapter 1 .... 1\nChapter 2 .... 2",
        metadata={"source": "test"}
    )

    new_metadata = enrich_metadata(doc)

    assert "is_toc" in new_metadata
    assert "toc_score" in new_metadata
    assert "toc_threshold_used" in new_metadata

    assert isinstance(new_metadata["is_toc"], bool)
    assert isinstance(new_metadata["toc_score"], float)
    assert new_metadata["toc_threshold_used"] == TOC_THRESHOLD


def test_enrich_metadata_preserves_original_metadata():
    doc = Document(
        page_content="Normal text",
        metadata={"source": "file.pdf", "page": 1}
    )

    new_metadata = enrich_metadata(doc)

    assert new_metadata["source"] == "file.pdf"
    assert new_metadata["page"] == 1