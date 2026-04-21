# ---- TABLE ----
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS semantic_memory (
  id SERIAL PRIMARY KEY,

  user_id TEXT NOT NULL,
  session_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,

  embedding VECTOR(1024),

  created_at TIMESTAMP DEFAULT NOW()
);
"""

# ---- Vector Index (HNSW) ----
CREATE_VECTOR_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_semantic_memory_vector_hnsw
ON semantic_memory
USING hnsw (embedding vector_cosine_ops);
"""

# ---- Full Text Index (FTS) ----
CREATE_FTS_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_semantic_memory_fts
ON semantic_memory
USING GIN (
  to_tsvector('simple', coalesce(content,''))
);
"""

# ---- INSERT ----
INSERT_MESSAGE = """
INSERT INTO semantic_memory (
    user_id,
    session_id,
    role,
    content,
    embedding
)
VALUES (%s, %s, %s, %s, %s);
"""


# ---- HISTORY ----
GET_USER_HISTORY = """
SELECT *
FROM semantic_memory
WHERE user_id = %s
  AND session_id = %s
ORDER BY created_at DESC
LIMIT 50;
"""


# ---- STM ----
GET_STM = """
SELECT *
FROM semantic_memory
WHERE user_id = %s
  AND session_id = %s
ORDER BY created_at DESC
LIMIT %s;
"""


# ---- COUNT ----
COUNT_ROWS = """
SELECT COUNT(*) AS total
FROM semantic_memory;
"""


# ---- HEALTH CHECK ----
HEALTH_CHECK = """
SELECT to_regclass('public.semantic_memory');
"""


# ---- DELETE ALL ----
DELETE_ALL = """
DELETE FROM semantic_memory;
"""


# ---- DROP TABLE ----
DROP_TABLE = """
DROP TABLE IF EXISTS semantic_memory;
"""


# ---- BM25 SEARCH ----
BM25_SEARCH = """
WITH docs AS (
    SELECT
        id,
        user_id,
        session_id,
        role,
        content,
        created_at,
        setweight(to_tsvector('simple', coalesce(content,'')), 'A') AS tsv
    FROM semantic_memory
    WHERE user_id = %s
      AND session_id = %s
)
SELECT
    id,
    user_id,
    session_id,
    role,
    content,
    created_at,
    ts_rank_cd(
        tsv,
        to_tsquery('simple', replace(%s, ' ', ' | '))
    ) AS bm25_score
FROM docs
WHERE tsv @@ to_tsquery('simple', replace(%s, ' ', ' | '))
ORDER BY bm25_score DESC
LIMIT %s;
"""


# ---- VECTOR SEARCH ----
VECTOR_SEARCH = """
SELECT
    id,
    user_id,
    session_id,
    role,
    content,
    created_at,
    1 - (embedding <=> %s::vector) AS vector_score
FROM semantic_memory
WHERE user_id = %s
  AND session_id = %s
  AND embedding IS NOT NULL
ORDER BY embedding <=> %s::vector
LIMIT %s;
"""