# ---- Memory Transactions Queries ----

# ---- EXTENSION (MUST BE FIRST) ----
CREATE_EXTENSION = """
CREATE EXTENSION IF NOT EXISTS vector;
"""

# ---- TABLE ----
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS memory_transactions (
    id BIGSERIAL PRIMARY KEY,

    user_id TEXT NOT NULL,

    product TEXT,
    category TEXT,

    amount NUMERIC,
    quantity NUMERIC,
    currency TEXT,

    note TEXT,
    raw_input TEXT NOT NULL,

    embedding VECTOR(1024),

    created_at TIMESTAMP DEFAULT NOW()
);
"""

# ---- INDEX ----
CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_memory_tx_user_time
ON memory_transactions(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_memory_tx_category
ON memory_transactions(category);

CREATE INDEX IF NOT EXISTS idx_memory_tx_product
ON memory_transactions(product);

CREATE INDEX IF NOT EXISTS idx_memory_tx_embedding
ON memory_transactions
USING hnsw (embedding vector_cosine_ops);
"""

# ---- INSERT EVENT ----
INSERT_EVENT = """
INSERT INTO memory_transactions (
    user_id,
    product,
    category,
    amount,
    quantity,
    currency,
    note,
    raw_input,
    embedding
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
"""

# ---- GET USER EVENTS ----
GET_USER_EVENTS = """
SELECT *
FROM memory_transactions
WHERE user_id = %s
ORDER BY created_at DESC;
"""

# ---- GET BY CATEGORY ----
GET_BY_CATEGORY = """
SELECT *
FROM memory_transactions
WHERE user_id = %s AND category = %s
ORDER BY created_at DESC;
"""

# ---- COUNT ----
COUNT_ROWS = """
SELECT COUNT(*) AS total
FROM memory_transactions;
"""