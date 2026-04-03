import pytest
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.modules.ingestion.chunker.spiltter import Splitter


pytestmark = pytest.mark.chunk_splitter

# ---------- Fixtures ----------

@pytest.fixture
def splitter():
    return Splitter(chunk_size=100, chunk_overlap=20)


@pytest.fixture
def sample_text():
    return "This is a test text. " * 50


# ---------- Tests ----------

def test_splitter_initialization():
    s = Splitter(chunk_size=200, chunk_overlap=50)

    assert s.chunk_size == 200
    assert s.chunk_overlap == 50


def test_get_splitter_returns_correct_type(splitter, sample_text):
    result = splitter.get_splitter(sample_text)

    assert isinstance(result, RecursiveCharacterTextSplitter)


def test_splitter_configuration(splitter, sample_text):
    result = splitter.get_splitter(sample_text)

    assert result._chunk_size == splitter.chunk_size
    assert result._chunk_overlap == splitter.chunk_overlap
    assert result._length_function == len
    assert result._is_separator_regex is False
    assert result._separators == ["\n\n", "\n", " ", ""]


def test_text_is_split_into_chunks(splitter, sample_text):
    text_splitter = splitter.get_splitter(sample_text)

    chunks = text_splitter.split_text(sample_text)

    assert isinstance(chunks, list)
    assert len(chunks) > 1


def test_chunk_size_respected(splitter):
    long_text = "a" * 1000
    text_splitter = splitter.get_splitter(long_text)

    chunks = text_splitter.split_text(long_text)

    for chunk in chunks:
        assert len(chunk) <= splitter.chunk_size


def test_overlap_effect(splitter):
    text_splitter = splitter.get_splitter("a " * 500)

    chunks = text_splitter.split_text("a " * 500)

    if len(chunks) > 1:
        assert len(set(chunks[0]).intersection(set(chunks[1]))) > 0