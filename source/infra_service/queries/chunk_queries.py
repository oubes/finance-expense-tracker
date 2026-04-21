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
"""


# ---- Vector Index (HNSW) ----
CREATE_VECTOR_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_chunks_table_vector_hnsw
ON chunks_table
USING hnsw (embedding vector_cosine_ops);
"""


# ---- Full Text Index (BM25 FIXED) ----
CREATE_FTS_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_chunks_table_fts
ON chunks_table
USING GIN (
    to_tsvector('simple', coalesce(content,'') || ' ' || coalesce(summary,''))
);
"""


# ---- Created At Index (performance for stm/history) ----
CREATE_CREATED_AT_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_chunks_table_created_at
ON chunks_table (created_at DESC);
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


# ---- BM25 SEARCH (uses generated column) ----
BM25_SEARCH_SQL = """
WITH q AS (
    SELECT plainto_tsquery('simple', %s) AS query
),
docs AS (
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
        fts
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
    COALESCE(ts_rank_cd(fts, q.query), 0) AS bm25_score
FROM docs, q
WHERE fts @@ q.query
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
    score,
    embedding <=> %s::vector AS distance
FROM chunks_table
WHERE embedding IS NOT NULL
ORDER BY distance ASC
LIMIT %s;
"""


# ---- Delete ----
DELETE_CHUNKS_SQL = "DELETE FROM chunks_table;"


# ---- Drop (SAFE) ----
DROP_CHUNKS_TABLE_SQL = "DROP TABLE IF EXISTS chunks_table;"


# ---- Count ----
COUNT_CHUNKS_SQL = "SELECT COUNT(*) FROM chunks_table;"


# ---- Health Check ----
TABLE_EXISTS_SQL = "SELECT to_regclass('public.chunks_table');"