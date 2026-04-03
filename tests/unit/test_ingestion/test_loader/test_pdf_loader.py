import pytest
from unittest.mock import MagicMock, patch

from src.modules.ingestion.loader.pdf_loader import PDFDocumentLoader


pytestmark = pytest.mark.pdf_loader

# ---------- Fixtures ----------

@pytest.fixture
def loader(tmp_path):
    return PDFDocumentLoader(data_dir=str(tmp_path))


# ---------- Tests ----------

def test_load_pdf_file_not_found(loader):
    with pytest.raises(FileNotFoundError):
        loader.load_pdf("non_existing.pdf")


@patch("src.modules.ingestion.loader.pdf_loader.PyPDFLoader")
def test_load_pdf_success(mock_loader_class, loader, tmp_path):
    # Arrange
    fake_documents = ["doc1", "doc2"]

    mock_loader_instance = MagicMock()
    mock_loader_instance.load.return_value = fake_documents
    mock_loader_class.return_value = mock_loader_instance

    file_name = "test.pdf"
    file_path = tmp_path / file_name
    file_path.touch()  # create empty file so exists() passes

    # Act
    result = loader.load_pdf(file_name)

    # Assert
    assert result == fake_documents
    mock_loader_class.assert_called_once_with(str(file_path))
    mock_loader_instance.load.assert_called_once()


@patch("src.modules.ingestion.loader.pdf_loader.PyPDFLoader")
def test_load_pdf_returns_list_of_documents(mock_loader_class, loader, tmp_path):
    mock_loader_instance = MagicMock()
    mock_loader_instance.load.return_value = ["doc"]
    mock_loader_class.return_value = mock_loader_instance

    file_name = "test.pdf"
    (tmp_path / file_name).touch()

    result = loader.load_pdf(file_name)

    assert isinstance(result, list)
    assert len(result) == 1


@patch("src.modules.ingestion.loader.pdf_loader.PyPDFLoader")
def test_load_pdf_propagates_exception(mock_loader_class, loader, tmp_path):
    mock_loader_instance = MagicMock()
    mock_loader_instance.load.side_effect = Exception("PDF load error")
    mock_loader_class.return_value = mock_loader_instance

    file_name = "test.pdf"
    (tmp_path / file_name).touch()

    with pytest.raises(Exception):
        loader.load_pdf(file_name)