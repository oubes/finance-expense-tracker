from src.modules.ingestion.chunker.scoring import score_chunk

def build_chunk(
    content: str,
    doc_name: str,
    meta: dict,
    chunk_index: int,
    raw_content: str,
) -> dict:
    page = meta["page"]

    score = score_chunk(content, raw_text=raw_content)

    return {
        "content": content,
        "doc_name": doc_name,
        "page": page,
        "chunk_index": chunk_index,
        "section": f"page_{page}_chunk_{chunk_index}",
        "score": score,
        "source": meta.get("source", "unknown"),

        "is_toc": meta.get("is_toc", False),
        "toc_score": meta.get("toc_score", 0),
    }