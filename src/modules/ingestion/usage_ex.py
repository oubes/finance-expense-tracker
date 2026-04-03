from src.modules.ingestion.loader.pdf_loader import PDFDocumentLoader
from src.modules.ingestion.chunker.chunker import Chunker

loader = PDFDocumentLoader()
chunker = Chunker()

doc_name = "Millennial_Playbook_Full.pdf"
docs = loader.load_pdf(doc_name)

chunks = chunker.chunk_documents(
    documents=docs,
    doc_name=doc_name
)

for i in range(50):
    print(chunks[i], end=f"\n\n{'-' * 100}\n\n")