# ---- Create Table ----
CREATE_CHUNKS_TABLE_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunk_embeddings (
    id UUID PRIMARY KEY,
    doc_id TEXT,
    chunk_id UUID,

    content TEXT,
    summary TEXT,
    embedding VECTOR({dim}) NOT NULL,

    chunk_title TEXT,
    section TEXT,

    doc_title TEXT,
    source TEXT,

    page INT,
    total_pages INT,

    tags TEXT[],

    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,

    created_at TIMESTAMP WITH TIME ZONE,
    pipeline_version TEXT
);

CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_vector_hnsw
ON chunk_embeddings
USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_metadata_gin
ON chunk_embeddings
USING GIN (metadata);
"""

# ---- Upsert ----
INSERT_CHUNK_SQL = """
INSERT INTO chunk_embeddings (
    id, doc_id, chunk_id,
    content, summary, embedding,
    chunk_title, section,
    doc_title, source,
    page, total_pages,
    tags,
    metadata,
    created_at,
    pipeline_version
)
VALUES (
    %s, %s, %s,
    %s, %s, %s,
    %s, %s,
    %s, %s,
    %s, %s,
    %s,
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
    section = EXCLUDED.section,
    metadata = EXCLUDED.metadata;
"""

# ---- Vector Search ----
SEARCH_CHUNKS_SQL = """
SELECT 
    id,
    content,
    summary,
    metadata,
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
SELECT id, content, metadata
FROM chunk_embeddings
LIMIT %s;
"""