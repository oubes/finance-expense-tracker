# ---- Memory Transactions Queries ----


# ---- TABLE ----
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS memory_transactions (
    id SERIAL PRIMARY KEY,

    user_id TEXT NOT NULL,
    domain TEXT NOT NULL,          -- facts | tags | chunks | conversation
    operation TEXT NOT NULL,       -- insert | update | delete

    payload JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);
"""


# ---- INDEX ----
CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_memory_tx_user_domain
ON memory_transactions(user_id, domain);
"""


# ---- INSERT EVENT ----
INSERT_EVENT = """
INSERT INTO memory_transactions (
    user_id,
    domain,
    operation,
    payload
)
VALUES ($1, $2, $3, $4);
"""


# ---- GET USER EVENTS ----
GET_USER_EVENTS = """
SELECT *
FROM memory_transactions
WHERE user_id = $1
ORDER BY created_at DESC;
"""


# ---- GET BY DOMAIN ----
GET_BY_DOMAIN = """
SELECT *
FROM memory_transactions
WHERE user_id = $1 AND domain = $2
ORDER BY created_at DESC;
"""


# ---- COUNT ----
COUNT_ROWS = """
SELECT COUNT(*) AS total
FROM memory_transactions;
"""