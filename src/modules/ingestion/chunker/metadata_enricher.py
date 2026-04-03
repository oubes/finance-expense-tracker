from langchain_core.documents import Document


def enrich_metadata(doc: Document) -> dict:
    return {
        "page": doc.metadata.get("page", -1),
        "source": doc.metadata.get("source"),
    }