# ---- User Facts Queries ----
# ---- TABLE CREATION ----
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS user_facts (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,

    income NUMERIC,
    currency TEXT DEFAULT 'EGP',

    rent NUMERIC,
    food_expense NUMERIC,
    fixed_expenses NUMERIC,
    disposable_income NUMERIC,

    confidence REAL,
    raw_json JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);
"""


# ---- INDEXING ----
CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_user_facts_user_id_created_at
ON user_facts(user_id, created_at DESC);
"""


# ---- INSERT (NEW VERSION) ----
INSERT_FACTS = """
INSERT INTO user_facts (
    user_id,
    income,
    currency,
    rent,
    food_expense,
    fixed_expenses,
    disposable_income,
    confidence,
    raw_json
)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9);
"""


# ---- GET LATEST FACT ----
GET_LATEST_BY_USER_ID = """
SELECT *
FROM user_facts
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT 1;
"""


# ---- GET FULL HISTORY ----
GET_HISTORY_BY_USER_ID = """
SELECT *
FROM user_facts
WHERE user_id = $1
ORDER BY created_at DESC;
"""


# ---- COUNT GLOBAL ----
COUNT_ROWS = """
SELECT COUNT(*) AS total
FROM user_facts;
"""


# ---- COUNT PER USER ----
COUNT_BY_USER = """
SELECT COUNT(*) AS total
FROM user_facts
WHERE user_id = $1;
"""