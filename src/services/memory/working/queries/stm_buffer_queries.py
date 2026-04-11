# ---- STM Buffer Queries ----


# ---- TABLE ----
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS stm_buffer (
    id SERIAL PRIMARY KEY,

    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,

    payload JSONB NOT NULL,

    created_at TIMESTAMP DEFAULT NOW()
);
"""


# ---- INDEX ----
CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_stm_buffer_session
ON stm_buffer(session_id);
"""


# ---- PUSH ----
PUSH = """
INSERT INTO stm_buffer (
    session_id,
    user_id,
    payload
)
VALUES ($1,$2,$3);
"""


# ---- POP (oldest first) ----
POP = """
DELETE FROM stm_buffer
WHERE id IN (
    SELECT id
    FROM stm_buffer
    WHERE session_id = $1
    ORDER BY created_at ASC
    LIMIT 1
)
RETURNING *;
"""


# ---- GET ALL ----
GET_ALL = """
SELECT *
FROM stm_buffer
WHERE session_id = $1
ORDER BY created_at ASC;
"""


# ---- CLEAR ----
CLEAR = """
DELETE FROM stm_buffer
WHERE session_id = $1;
"""