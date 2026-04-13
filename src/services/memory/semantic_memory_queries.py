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


# ---- VECTOR SEARCH ----
VECTOR_SEARCH = """
SELECT *,
       embedding <-> %s AS distance
FROM semantic_memory
WHERE user_id = %s
ORDER BY distance ASC
LIMIT 10;
"""


# ---- COUNT ----
COUNT_ROWS = """
SELECT COUNT(*) AS total
FROM semantic_memory;
"""