# ---- Tags Queries ----


# ---- TABLE ----
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS user_tags (
    id SERIAL PRIMARY KEY,

    user_id TEXT NOT NULL,
    tag TEXT NOT NULL,

    confidence REAL DEFAULT 1.0,

    created_at TIMESTAMP DEFAULT NOW()
);
"""


# ---- INDEX ----
CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_user_tags_user_id
ON user_tags(user_id);
"""


# ---- INSERT TAG ----
INSERT_TAG = """
INSERT INTO user_tags (
    user_id,
    tag,
    confidence
)
VALUES ($1, $2, $3);
"""


# ---- GET TAGS ----
GET_TAGS_BY_USER = """
SELECT *
FROM user_tags
WHERE user_id = $1
ORDER BY confidence DESC;
"""


# ---- DELETE TAGS ----
DELETE_TAGS = """
DELETE FROM user_tags
WHERE user_id = $1;
"""


# ---- COUNT ----
COUNT_ROWS = """
SELECT COUNT(*) AS total
FROM user_tags;
"""