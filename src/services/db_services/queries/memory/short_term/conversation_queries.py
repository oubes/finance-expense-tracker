# ---- Conversation Queries ----


# ---- TABLE ----
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,

    role TEXT NOT NULL,
    content TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT NOW()
);
"""


# ---- INDEX ----
CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_conversations_session_time
ON conversations(session_id, created_at DESC);
"""


# ---- INSERT MESSAGE ----
INSERT_MESSAGE = """
INSERT INTO conversations (
    session_id,
    user_id,
    role,
    content
)
VALUES ($1,$2,$3,$4);
"""


# ---- GET SESSION HISTORY ----
GET_HISTORY = """
SELECT *
FROM conversations
WHERE session_id = $1
ORDER BY created_at DESC
LIMIT 50;
"""


# ---- GET USER RECENT ACTIVITY ----
GET_USER_RECENT = """
SELECT *
FROM conversations
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT 50;
"""


# ---- DELETE SESSION ----
DELETE_SESSION = """
DELETE FROM conversations
WHERE session_id = $1;
"""


# ---- COUNT ----
COUNT_ROWS = """
SELECT COUNT(*) AS total
FROM conversations;
"""