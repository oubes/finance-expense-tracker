# ---- Create Table ----
CREATE_CHUNKS_TABLE_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunk_embeddings (
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
    pipeline_version TEXT
);

CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_vector_hnsw
ON chunk_embeddings
USING hnsw (embedding vector_cosine_ops);
"""


# ---- Upsert ----
INSERT_CHUNK_SQL = """
INSERT INTO chunk_embeddings (
    id, chunk_id,
    content, summary, embedding,
    chunk_title,
    doc_title, source,
    page, total_pages,
    created_at,
    pipeline_version
)
VALUES (
    %s, %s, %s,
    %s, %s, %s,
    %s, %s, %s,
    %s, %s, %s
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
    pipeline_version = EXCLUDED.pipeline_version;
"""


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


# ---- Delete ----
DELETE_CHUNKS_SQL = "DELETE FROM chunk_embeddings;"


# ---- Count ----
COUNT_CHUNKS_SQL = "SELECT COUNT(*) FROM chunk_embeddings;"


# ---- Preview ----
PREVIEW_CHUNKS_SQL = """
SELECT id, content
FROM chunk_embeddings
LIMIT %s;
"""