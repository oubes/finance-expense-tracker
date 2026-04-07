# ---- Create Table ----
CREATE_CHUNKS_TABLE_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunk_embeddings (
    id TEXT PRIMARY KEY,
    vector VECTOR({dim}) NOT NULL,
    text TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_vector_hnsw
ON chunk_embeddings
USING hnsw (vector vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_metadata_gin
ON chunk_embeddings
USING GIN (metadata);
"""

# ---- Insert (Upsert) ----
INSERT_CHUNK_SQL = """
INSERT INTO chunk_embeddings (id, vector, text, metadata)
VALUES (%s, %s, %s, %s)
ON CONFLICT (id)
DO UPDATE SET
    vector = EXCLUDED.vector,
    text = EXCLUDED.text,
    metadata = EXCLUDED.metadata;
"""

# ---- Vector Search ----
SEARCH_CHUNKS_SQL = """
SELECT 
    id,
    text,
    metadata,
    1 - (vector <=> %s::vector) AS cosine_sim
FROM chunk_embeddings
WHERE (%s::text IS NULL OR metadata->>'doc_title' = %s)
ORDER BY vector <=> %s::vector
LIMIT %s;
"""

# ---- Keyword Search ----
KEYWORD_SEARCH_CHUNKS_SQL = """
SELECT 
    id,
    text,
    metadata,
    ts_rank_cd(
        to_tsvector('english', text),
        plainto_tsquery('english', %s)
    ) AS score
FROM chunk_embeddings
WHERE to_tsvector('english', text) @@ plainto_tsquery('english', %s)
ORDER BY score DESC
LIMIT %s;
"""

# ---- Delete All ----
DELETE_CHUNKS_SQL = """
DELETE FROM chunk_embeddings;
"""

# ---- Count ----
COUNT_CHUNKS_SQL = """
SELECT COUNT(*) FROM chunk_embeddings;
"""

# ---- Preview ----
PREVIEW_CHUNKS_SQL = """
SELECT id, text, metadata
FROM chunk_embeddings
LIMIT %s;
"""