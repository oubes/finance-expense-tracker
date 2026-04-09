# ---- RAG Queries ----

# ---- Vector Search ----
SEARCH_CHUNKS_SQL = """
SELECT 
    id,
    content,
    summary,
    1 - (embedding <=> %s::vector) AS cosine_sim
FROM chunk_embeddings
WHERE (%s::text IS NULL OR doc_title = %s)
ORDER BY embedding <=> %s::vector
LIMIT %s;
"""


# ---- Preview ----
PREVIEW_CHUNKS_SQL = """
SELECT id, content
FROM chunk_embeddings
LIMIT %s;
"""