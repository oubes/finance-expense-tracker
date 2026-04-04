import pytest

from src.bootstrap.dependencies import get_chunker_splitter, get_settings

pytestmark = pytest.mark.unit


# ---- Fixtures ----
@pytest.fixture
def splitter():
    return get_chunker_splitter()


@pytest.fixture
def settings():
    return get_settings()


@pytest.fixture
def sample_text():
    return "This is a test text. " * 50


# ---------- Tests ----------

def test_splitter_initialization(settings):
    splitter = get_chunker_splitter()

    assert hasattr(splitter, "chunk_size")
    assert hasattr(splitter, "chunk_overlap")

    assert splitter.chunk_size == settings.rag.chunk_size
    assert splitter.chunk_overlap == settings.rag.chunk_overlap


def test_splitter_returns_chunks(splitter, sample_text):
    chunks = splitter.split(sample_text)

    assert isinstance(chunks, list)
    assert len(chunks) > 1
    assert all(isinstance(c, str) for c in chunks)


def test_text_is_split_into_chunks(splitter, sample_text):
    chunks = splitter.split(sample_text)

    assert isinstance(chunks, list)
    assert len(chunks) > 1


def test_chunk_size_respected(splitter):
    long_text = "a" * 1000
    chunks = splitter.split(long_text)

    for chunk in chunks:
        assert len(chunk) <= splitter.chunk_size


def test_overlap_effect(splitter):
    text = "a " * 500
    chunks = splitter.split(text)

    if len(chunks) > 1:
        overlap_exists = len(set(chunks[0]).intersection(set(chunks[1]))) > 0
        assert overlap_exists