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

CREATE INDEX IF NOT EXISTS idx_conversations_user_time
ON conversations(user_id, created_at DESC);
"""

# ---- INSERT MESSAGE ----
INSERT_MESSAGE = """
INSERT INTO conversations (
    session_id,
    user_id,
    role,
    content
)
VALUES (%s, %s, %s, %s);
"""

# ---- GET SESSION HISTORY ----
GET_HISTORY = """
SELECT *
FROM conversations
WHERE session_id = %s
ORDER BY created_at DESC
LIMIT 50;
"""

# ---- GET USER RECENT ACTIVITY ----
GET_USER_RECENT = """
SELECT *
FROM conversations
WHERE user_id = %s
ORDER BY created_at DESC
LIMIT 50;
"""

# ---- GET STM (LAST N MESSAGES - MEMORY LAYER) ----
GET_STM = """
SELECT *
FROM (
    SELECT *
    FROM conversations
    WHERE user_id = %s
    ORDER BY created_at DESC
    LIMIT %s
) sub
ORDER BY created_at ASC;
"""

# ---- DELETE SESSION ----
DELETE_SESSION = """
DELETE FROM conversations
WHERE session_id = %s;
"""

# ---- COUNT ----
COUNT_ROWS = """
SELECT COUNT(*) AS total
FROM conversations;
"""