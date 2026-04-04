import pytest
from unittest.mock import MagicMock

from src.modules.ingestion.loader.pdf_loader import PDFDocumentLoader
from src.bootstrap.dependencies import get_pdf_loader

pytestmark = pytest.mark.unit


# ---- Fixture ----
@pytest.fixture
def loader(tmp_path, monkeypatch) -> tuple[PDFDocumentLoader, MagicMock]:
    mock_backend = MagicMock()

    def fake_loader_instance(*args, **kwargs):
        instance = MagicMock()
        instance.load = mock_backend.load
        return instance

    # ---- Patch correct import path ----
    monkeypatch.setattr(
        "src.modules.ingestion.loader.pdf_loader.PyPDFLoader",
        fake_loader_instance,
    )

    # ---- Use factory without unsupported kwargs ----
    loader_instance = get_pdf_loader()

    # Inject data_dir manually for testing
    loader_instance.data_dir = tmp_path

    return loader_instance, mock_backend


# ---------- Tests ----------

def test_load_pdf_file_not_found(loader):
    pdf_loader, _ = loader

    with pytest.raises(FileNotFoundError):
        pdf_loader.load_pdf("non_existing.pdf")


def test_load_pdf_success(loader, tmp_path):
    pdf_loader, mock_backend = loader

    fake_documents = ["doc1", "doc2"]
    mock_backend.load.return_value = fake_documents

    file_name = "test.pdf"
    file_path = tmp_path / file_name
    file_path.touch()

    result = pdf_loader.load_pdf(file_name)

    assert result == fake_documents
    mock_backend.load.assert_called_once()


def test_load_pdf_returns_list_of_documents(loader, tmp_path):
    pdf_loader, mock_backend = loader

    mock_backend.load.return_value = ["doc"]

    file_name = "test.pdf"
    (tmp_path / file_name).touch()

    result = pdf_loader.load_pdf(file_name)

    assert isinstance(result, list)
    assert len(result) == 1


def test_load_pdf_propagates_exception(loader, tmp_path):
    pdf_loader, mock_backend = loader

    mock_backend.load.side_effect = Exception("PDF load error")

    file_name = "test.pdf"
    (tmp_path / file_name).touch()

    with pytest.raises(Exception):
        pdf_loader.load_pdf(file_name)