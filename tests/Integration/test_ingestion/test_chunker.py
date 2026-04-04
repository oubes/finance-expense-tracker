import pytest
from pathlib import Path
from langchain_core.documents import Document

from src.bootstrap.dependencies import (
    get_pdf_loader,
    get_chunker,
)

pytestmark = pytest.mark.integration


# ---- Fixture ----
@pytest.fixture
def integration_setup(tmp_path):
    loader = get_pdf_loader(data_dir="data/raw")
    chunker = get_chunker(base_chunk_size=500, chunk_overlap=50, min_length=30)
    return loader, chunker


# ---------- Full Pipeline ----------

def test_full_ingestion_pipeline(integration_setup):
    loader, chunker = integration_setup

    test_pdf = "Ai System Design Competition.pdf"
    pdf_path = Path("data/raw") / test_pdf

    if not pdf_path.exists():
        pytest.skip(f"Test file {test_pdf} not found.")

    # 1. Load
    documents = loader.load_pdf(test_pdf)

    # 2. Process
    chunks = chunker.chunk_documents(documents, doc_name=test_pdf)

    # 3. Assertions
    assert len(chunks) > 0

    first_chunk = chunks[0]

    assert "content" in first_chunk
    assert "doc_name" in first_chunk
    assert "chunk_index" in first_chunk
    assert first_chunk["doc_name"] == test_pdf


# ---------- Chunker with Mock Documents ----------

def test_chunker_with_mock_documents(integration_setup):
    _, chunker = integration_setup

    mock_docs = [
        Document(
            page_content="This is a valid long string to pass the min_length validation check.",
            metadata={"source": "manual", "page": 1},
        )
    ]

    chunks = chunker.chunk_documents(mock_docs, doc_name="mock_test")

    assert len(chunks) > 0
    assert chunks[0]["doc_name"] == "mock_test"


# ---------- Empty Input Handling ----------

def test_empty_input_handling(integration_setup):
    _, chunker = integration_setup

    chunks = chunker.chunk_documents([], doc_name="empty.pdf")

    assert chunks == []