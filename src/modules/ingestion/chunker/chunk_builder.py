from scoring import score_chunk


def build_chunk(
    content: str,
    doc_name: str,
    meta: dict,
    chunk_index: int,
) -> dict:
    page = meta["page"]

    return {
        "content": content,
        "doc_name": doc_name,
        "page": page,
        "chunk_index": chunk_index,
        "section": f"page_{page}_chunk_{chunk_index}",
        "score": score_chunk(content),
        "source": meta["source"],
    }