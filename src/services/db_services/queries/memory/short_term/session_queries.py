# ---- Session State Queries ----


# ---- TABLE ----
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS session_state (
    session_id TEXT PRIMARY KEY,

    user_id TEXT NOT NULL,
    status TEXT NOT NULL,   -- active | paused | closed

    current_step TEXT,
    flags JSONB,

    updated_at TIMESTAMP DEFAULT NOW()
);
"""


# ---- INDEX ----
CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_session_state_user
ON session_state(user_id);
"""


# ---- UPSERT STATE ----
SET_STATE = """
INSERT INTO session_state (
    session_id,
    user_id,
    status,
    current_step,
    flags,
    updated_at
)
VALUES ($1,$2,$3,$4,$5,NOW())
ON CONFLICT (session_id)
DO UPDATE SET
    status = EXCLUDED.status,
    current_step = EXCLUDED.current_step,
    flags = EXCLUDED.flags,
    updated_at = NOW();
"""


# ---- GET ----
GET_STATE = """
SELECT *
FROM session_state
WHERE session_id = $1;
"""


# ---- DELETE ----
DELETE_STATE = """
DELETE FROM session_state
WHERE session_id = $1;
"""