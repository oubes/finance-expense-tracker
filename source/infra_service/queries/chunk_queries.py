# ---- Chunk Queries ----

# ---- Create Table ----
CREATE_CHUNKS_TABLE_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks_table (
    id UUID PRIMARY KEY,
    chunk_id UUID,

    content TEXT,
    summary TEXT,

    embedding VECTOR({dim}) NOT NULL,

    chunk_title TEXT,

    doc_title TEXT,
    source TEXT,

    page INT,
    total_pages INT,

    created_at TIMESTAMP WITH TIME ZONE,
    pipeline_version TEXT,

    score FLOAT
);

CREATE INDEX IF NOT EXISTS idx_chunks_table_vector_hnsw
ON chunks_table
USING hnsw (embedding vector_cosine_ops);
"""


# ---- Upsert ----
INSERT_CHUNK_SQL = """
INSERT INTO chunks_table (
    id, chunk_id,
    content, summary, embedding,
    chunk_title,
    doc_title, source,
    page, total_pages,
    created_at,
    pipeline_version,
    score
)
VALUES (
    %s, %s, %s,
    %s, %s, %s,
    %s, %s, %s,
    %s, %s, %s,
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


# ---- Delete ----
DELETE_CHUNKS_SQL = "DELETE FROM chunks_table;"

# ---- Drop ----
DROP_CHUNKS_TABLE_SQL = "DROP TABLE chunks_table;"

# ---- Count ----
COUNT_CHUNKS_SQL = "SELECT COUNT(*) FROM chunks_table;"

# ---- Health Check ----
TABLE_EXISTS_SQL = "SELECT to_regclass('public.chunks_table');"