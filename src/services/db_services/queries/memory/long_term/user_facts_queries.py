# ---- User Facts Queries ----

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS user_facts (
    user_id TEXT PRIMARY KEY,

    income NUMERIC,
    currency TEXT DEFAULT 'EGP',

    rent NUMERIC,
    food_expense NUMERIC,

    fixed_expenses NUMERIC,
    disposable_income NUMERIC,

    last_updated TIMESTAMP,
    confidence REAL,

    raw_json JSONB
);
"""

CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_user_facts_user_id
ON user_facts(user_id);
"""


# ---- SELECT ----
GET_BY_USER_ID = """
SELECT * 
FROM user_facts
WHERE user_id = $1;
"""


# ---- INSERT ----
INSERT_FACTS = """
INSERT INTO user_facts (
    user_id, income, currency, rent, food_expense,
    fixed_expenses, disposable_income,
    last_updated, confidence, raw_json
)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10);
"""


# ---- UPDATE ----
UPDATE_FACTS = """
UPDATE user_facts
SET 
    income = $2,
    currency = $3,
    rent = $4,
    food_expense = $5,
    fixed_expenses = $6,
    disposable_income = $7,
    last_updated = $8,
    confidence = $9,
    raw_json = $10
WHERE user_id = $1;
"""


# ---- DELETE ----
DELETE_FACTS = """
DELETE FROM user_facts
WHERE user_id = $1;
"""


# ---- COUNT ----
COUNT_ROWS = """
SELECT COUNT(*) AS total
FROM user_facts;
"""