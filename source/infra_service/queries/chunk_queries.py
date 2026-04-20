# ---- Chunk Queries ----

# ---- Create Table ----
CREATE_CHUNKS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS chunks_table (
    id UUID PRIMARY KEY,

    content TEXT,
    summary TEXT,

    embedding VECTOR({dim}) NOT NULL,

    chunk_title TEXT,

    doc_title TEXT,
    source TEXT,

    page INT,
    total_pages INT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    pipeline_version TEXT,

    score FLOAT
);

-- ---- Vector Index (HNSW) ----
CREATE INDEX IF NOT EXISTS idx_chunks_table_vector_hnsw
ON chunks_table
USING hnsw (embedding vector_cosine_ops);

-- ---- Full Text Index (BM25) ----
CREATE INDEX IF NOT EXISTS idx_chunks_table_fts
ON chunks_table
USING GIN (
    setweight(to_tsvector('simple', coalesce(content,'')), 'A') ||
    setweight(to_tsvector('simple', coalesce(summary,'')), 'B')
);
"""


# ---- Upsert ----
INSERT_CHUNK_SQL = """
INSERT INTO chunks_table (
    id,
    content, summary, embedding,
    chunk_title,
    doc_title, source,
    page, total_pages,
    created_at,
    pipeline_version,
    score
)
VALUES (
    %s,
    %s, %s, %s,
    %s,
    %s, %s,
    %s, %s,
    %s,
    %s,
    %s
)
ON CONFLICT (id)
DO UPDATE SET
    content = EXCLUDED.content,
    summary = EXCLUDED.summary,
    embedding = EXCLUDED.embedding,
    chunk_title = EXCLUDED.chunk_title,
    doc_title = EXCLUDED.doc_title,
    source = EXCLUDED.source,
    page = EXCLUDED.page,
    total_pages = EXCLUDED.total_pages,
    created_at = EXCLUDED.created_at,
    pipeline_version = EXCLUDED.pipeline_version,
    score = EXCLUDED.score;
"""


# ---- BM25 SEARCH ----
BM25_SEARCH_SQL = """
WITH docs AS (
    SELECT
        id,
        content,
        summary,
        chunk_title,
        doc_title,
        source,
        page,
        total_pages,
        created_at,
        pipeline_version,
        score,
        (
            setweight(to_tsvector('simple', coalesce(content,'')), 'A') ||
            setweight(to_tsvector('simple', coalesce(summary,'')), 'B')
        ) AS tsv
    FROM chunks_table
)
SELECT
    id,
    content,
    summary,
    chunk_title,
    doc_title,
    source,
    page,
    total_pages,
    created_at,
    pipeline_version,
    score,
    COALESCE(
        ts_rank_cd(
            tsv,
            plainto_tsquery('simple', %s)
        ),
        0
    ) AS bm25_score
FROM docs
WHERE tsv @@ plainto_tsquery('simple', %s)
ORDER BY bm25_score DESC
LIMIT %s;
"""


# ---- VECTOR SEARCH ----
VECTOR_SEARCH_SQL = """
SELECT
    id,
    content,
    summary,
    chunk_title,
    doc_title,
    source,
    page,
    total_pages,
    created_at,
    pipeline_version,
    distance,
    1 / (1 + distance) AS vector_score
FROM (
    SELECT
        id,
        content,
        summary,
        chunk_title,
        doc_title,
        source,
        page,
        total_pages,
        created_at,
        pipeline_version,
        embedding <=> %s::vector AS distance
    FROM chunks_table
    WHERE embedding IS NOT NULL
) t
ORDER BY distance ASC
LIMIT %s;
"""


# ---- Delete ----
DELETE_CHUNKS_SQL = "DELETE FROM chunks_table;"


# ---- Drop ----
DROP_CHUNKS_TABLE_SQL = "DROP TABLE chunks_table;"


# ---- Count ----
COUNT_CHUNKS_SQL = "SELECT COUNT(*) FROM chunks_table;"


# ---- Health Check ----
TABLE_EXISTS_SQL = "SELECT to_regclass('public.chunks_table');"