import pytest
from pathlib import Path
from langchain_core.documents import Document

from src.bootstrap.dependencies import (
    get_pdf_loader,
    get_chunker,
    get_settings,
)

pytestmark = pytest.mark.integration


# ---- Fixtures ----
@pytest.fixture
def settings():
    return get_settings()


@pytest.fixture
def loader():
    return get_pdf_loader()


@pytest.fixture
def chunker():
    return get_chunker()


@pytest.fixture
def integration_setup(loader, chunker, settings):
    return loader, chunker, settings


# ---------- Full Pipeline ----------

def test_full_ingestion_pipeline(integration_setup):
    loader, chunker, _ = integration_setup

    test_pdf = "Ai System Design Competition.pdf"
    pdf_path = Path("data/raw") / test_pdf

    if not pdf_path.exists():
        pytest.skip(f"Test file {test_pdf} not found.")

    documents = loader.load_pdf(test_pdf)

    chunks = chunker.chunk_documents(
        documents,
        doc_name=test_pdf,
    )

    assert isinstance(chunks, list)
    assert len(chunks) > 0

    first_chunk = chunks[0]

    assert isinstance(first_chunk, dict)
    assert "content" in first_chunk
    assert "doc_name" in first_chunk
    assert "chunk_index" in first_chunk
    assert "metadata" in first_chunk
    assert "score" in first_chunk

    assert first_chunk["doc_name"] == test_pdf


# ---------- Chunker with Mock Documents ----------

def test_chunker_with_mock_documents(integration_setup):
    _, chunker, _ = integration_setup

    mock_docs = [
        Document(
            page_content="This is a valid long string to pass the min_length validation check.",
            metadata={"source": "manual", "page": 1},
        )
    ]

    chunks = chunker.chunk_documents(
        mock_docs,
        doc_name="mock_test",
    )

    assert isinstance(chunks, list)
    assert len(chunks) > 0

    chunk = chunks[0]
    assert chunk["doc_name"] == "mock_test"
    assert "content" in chunk
    assert "metadata" in chunk
    assert "score" in chunk


# ---------- Empty Input Handling ----------

def test_empty_input_handling(integration_setup):
    _, chunker, _ = integration_setup

    chunks = chunker.chunk_documents(
        [],
        doc_name="empty.pdf",
    )

    assert chunks == []