# ---- BM25 Query ----
BM25_QUERY = """
WITH docs AS (
    SELECT
        id,
        content,
        summary,
        chunk_title,
        doc_title,
        setweight(to_tsvector('simple', coalesce(doc_title,'')), 'A') ||
        setweight(to_tsvector('simple', coalesce(chunk_title,'')), 'B') ||
        setweight(to_tsvector('simple', coalesce(summary,'')), 'C') ||
        setweight(to_tsvector('simple', coalesce(content,'')), 'D') AS tsv
    FROM chunk_embeddings
)
SELECT
    id,
    content,
    summary,
    chunk_title,
    doc_title,
    ts_rank_cd(
        tsv,
        to_tsquery('simple', replace(%s, ' ', ' | '))
    ) AS score
FROM docs
WHERE tsv @@ to_tsquery('simple', replace(%s, ' ', ' | '))
ORDER BY score DESC
LIMIT %s;
"""


# ---- Vector Query ----
VECTOR_QUERY = """
SELECT
    id,
    content,
    summary,
    chunk_title,
    doc_title,
    score,
    1 - (embedding <=> %s::vector) AS vector_score
FROM chunk_embeddings
ORDER BY embedding <=> %s::vector
LIMIT %s;
"""