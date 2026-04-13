# ---- Memory Queries (Unified Minimal Memory Table) ----


# ---- TABLE ----
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS semantic_memory (
    id SERIAL PRIMARY KEY,

    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,

    embedding VECTOR,

    created_at TIMESTAMP DEFAULT NOW()
);
"""


# ---- INDEX ----
CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_semantic_memory_user_time
ON semantic_memory(user_id, created_at DESC);
"""


# ---- INSERT MESSAGE ----
INSERT_MESSAGE = """
INSERT INTO semantic_memory (
    user_id,
    role,
    content,
    embedding
)
VALUES (%s, %s, %s, %s);
"""


# ---- GET USER HISTORY ----
GET_USER_HISTORY = """
SELECT *
FROM semantic_memory
WHERE user_id = %s
ORDER BY created_at DESC
LIMIT 50;
"""


# ---- GET STM (RECENT CONTEXT) ----
GET_STM = """
SELECT *
FROM semantic_memory
WHERE user_id = %s
ORDER BY created_at DESC
LIMIT %s;
"""

# ---- COUNT ----
COUNT_ROWS = """
SELECT COUNT(*) AS total
FROM semantic_memory;
"""

# ---- BM25 SEARCH ----
BM25_SEARCH = """
WITH docs AS (
    SELECT
        id,
        user_id,
        role,
        content,
        created_at,
        setweight(to_tsvector('simple', coalesce(content,'')), 'A') AS tsv
    FROM semantic_memory
    WHERE user_id = %s
)
SELECT
    id,
    user_id,
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
    role,
    content,
    created_at,
    1 - (embedding <=> %s::vector) AS vector_score
FROM semantic_memory
WHERE user_id = %s
  AND embedding IS NOT NULL
ORDER BY embedding <=> %s::vector
LIMIT %s;
"""