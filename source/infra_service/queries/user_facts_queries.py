# ---- User Facts Queries ----

# ---- TABLE ----
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS user_facts_table (
    id SERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    income NUMERIC,
    currency TEXT DEFAULT 'EGP',
    rent NUMERIC,
    food_expense NUMERIC,
    fixed_expenses NUMERIC,
    disposable_income NUMERIC,
    created_at TIMESTAMP DEFAULT NOW()
);
"""


# ---- INDEX ----
CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_user_facts_user_id
ON user_facts_table(user_id);
"""


# ---- UPSERT (INSERT OR UPDATE) ----
UPSERT_FACTS_SQL = """
INSERT INTO user_facts_table (
    user_id, income, currency, rent, food_expense, fixed_expenses, disposable_income
)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (user_id) DO UPDATE SET
    income = EXCLUDED.income,
    currency = EXCLUDED.currency,
    rent = EXCLUDED.rent,
    food_expense = EXCLUDED.food_expense,
    fixed_expenses = EXCLUDED.fixed_expenses,
    disposable_income = EXCLUDED.disposable_income,
    created_at = NOW();
"""

# ---- UPDATE ----
UPDATE_FACTS_SQL = """
UPDATE user_facts_table SET
    income = %s,
    currency = %s,
    rent = %s,
    food_expense = %s,
    fixed_expenses = %s,
    disposable_income = %s,
    created_at = NOW()
WHERE user_id = %s;
"""


# ---- GET USER FACTS ----
GET_USER_FACTS_SQL = """
SELECT *
FROM user_facts_table
WHERE user_id = %s
LIMIT 1;
"""




# ---- COUNT GLOBAL ----
COUNT_ROWS_SQL = "SELECT COUNT(*) FROM user_facts_table;"


# ---- COUNT PER USER ----
COUNT_BY_USER_SQL = """
SELECT COUNT(*)
FROM user_facts_table
WHERE user_id = %s;
"""


# ---- DELETE ----
DELETE_ALL_SQL = "DELETE FROM user_facts_table;"


# ---- DROP ----
DROP_TABLE_SQL = "DROP TABLE IF EXISTS user_facts_table;"


# ---- HEALTH ----
TABLE_EXISTS_SQL = "SELECT to_regclass('public.user_facts_table');"