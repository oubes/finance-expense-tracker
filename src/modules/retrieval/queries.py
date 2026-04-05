# ---- BM25 Search Query ----
BM25_SEARCH_QUERY = """
SELECT id, content,
       ts_rank_cd(content_tsv, plainto_tsquery(%s)) AS score
FROM documents
WHERE content_tsv @@ plainto_tsquery(%s)
ORDER BY score DESC
LIMIT %s;
"""


# ---- Vector Search Query ----
VECTOR_SEARCH_QUERY = """
SELECT id, content,
       embedding <-> %s AS distance
FROM documents
ORDER BY embedding <-> %s
LIMIT %s;
"""