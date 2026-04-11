# ---- Transactions Queries ----

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS user_transactions (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,

    amount NUMERIC NOT NULL,
    category TEXT,
    description TEXT,

    transaction_type TEXT, -- expense | income

    created_at TIMESTAMP DEFAULT NOW()
);
"""

CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_user_transactions_user_id
ON user_transactions(user_id);
"""

# ---- INSERT ----
INSERT_TRANSACTION = """
INSERT INTO user_transactions (
    user_id, amount, category, description,
    transaction_type, created_at
)
VALUES ($1,$2,$3,$4,$5,$6);
"""

# ---- UPDATE ----
UPDATE_TRANSACTION = """
UPDATE user_transactions
SET 
    amount = $2,
    category = $3,
    description = $4,
    transaction_type = $5,
    created_at = $6
WHERE id = $1 AND user_id = $7;
"""

# ---- DELETE ----
DELETE_TRANSACTION = """
DELETE FROM user_transactions
WHERE id = $1 AND user_id = $2;
"""

# ---- FETCH BY USER ----
GET_BY_USER = """
SELECT *
FROM user_transactions
WHERE user_id = $1
ORDER BY created_at DESC;
"""

# ---- COUNT ----
COUNT_BY_USER = """
SELECT COUNT(*) AS total
FROM user_transactions
WHERE user_id = $1;
"""