# ---- Transactions Queries ----

# ---- TABLE ----
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS transactions_table (
    id BIGSERIAL PRIMARY KEY,

    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,

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

# ---- INDEXES ----
CREATE_USER_TIME_INDEX = """
CREATE INDEX IF NOT EXISTS idx_transactions_user_time
ON transactions_table(user_id, created_at DESC);
"""

CREATE_CATEGORY_INDEX = """
CREATE INDEX IF NOT EXISTS idx_transactions_category
ON transactions_table(category);
"""

CREATE_PRODUCT_INDEX = """
CREATE INDEX IF NOT EXISTS idx_transactions_product
ON transactions_table(product);
"""

CREATE_VECTOR_INDEX = """
CREATE INDEX IF NOT EXISTS idx_transactions_embedding
ON transactions_table
USING hnsw (embedding vector_cosine_ops);
"""

# ---- INSERT ----
INSERT_EVENT = """
INSERT INTO transactions_table (
    user_id,
    session_id,
    product,
    category,
    amount,
    quantity,
    currency,
    note,
    raw_input,
    embedding
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
"""

# ---- BM25 (UNIFIED SEARCH SPACE) ----
BM25_SEARCH = """
WITH docs AS (
    SELECT
        id,
        user_id,
        session_id,
        product,
        category,
        amount,
        quantity,
        currency,
        note,
        raw_input,
        created_at,

        (
            setweight(to_tsvector('simple', coalesce(product,'')), 'A') ||
            setweight(to_tsvector('simple', coalesce(category,'')), 'A') ||
            setweight(to_tsvector('simple', coalesce(note,'')), 'B') ||
            setweight(to_tsvector('simple', coalesce(raw_input,'')), 'B')
        ) AS tsv
    FROM transactions_table
    WHERE user_id = %s AND session_id = %s
)
SELECT
    *,
    ts_rank_cd(
        tsv,
        plainto_tsquery('simple', %s)
    ) AS bm25_score
FROM docs
WHERE tsv @@ plainto_tsquery('simple', %s)
ORDER BY bm25_score DESC
LIMIT %s;
"""

# ---- VECTOR SEARCH (UNIFIED EMBEDDING SPACE) ----
VECTOR_SEARCH = """
SELECT
    id,
    user_id,
        session_id,
    product,
    category,
    amount,
    quantity,
    currency,
    note,
    raw_input,
    created_at,

    1 - (embedding <=> %s::vector) AS vector_score

FROM transactions_table
WHERE user_id = %s
    AND session_id = %s
    AND embedding IS NOT NULL

ORDER BY embedding <=> %s::vector
LIMIT %s;
"""

# ---- COUNT ----
COUNT_ROWS = """
SELECT COUNT(*) AS total
FROM transactions_table;
"""

# ---- HEALTH CHECK ----
HEALTH_CHECK = """
SELECT to_regclass('public.transactions_table');
"""

# ---- DELETE ALL ----
DELETE_ALL = """
DELETE FROM transactions_table;
"""

# ---- DROP TABLE ----
DROP_TABLE = """
DROP TABLE IF EXISTS transactions_table;
"""