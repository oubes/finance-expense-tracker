from modules.ingestion.loader.document_loader import PDFDocumentLoader
from modules.ingestion.chunker.chunker import Chunker

loader = PDFDocumentLoader()
chunker = Chunker()

docs = loader.load_pdf("Ai System Design Competition.pdf")

chunks = chunker.chunk_documents(
    documents=docs,
    doc_name="ai_system_design"
)

print(chunks[0], "\n\n")
print(chunks[1])