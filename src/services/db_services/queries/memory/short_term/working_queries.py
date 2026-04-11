# ---- Working Memory Queries ----


# ---- TABLE ----
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS working_memory (
    session_id TEXT PRIMARY KEY,

    state JSONB NOT NULL,

    updated_at TIMESTAMP DEFAULT NOW()
);
"""


# ---- INDEX ----
CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_working_memory_session
ON working_memory(session_id);
"""


# ---- UPSERT STATE ----
SET_STATE = """
INSERT INTO working_memory (
    session_id,
    state,
    updated_at
)
VALUES ($1, $2, NOW())
ON CONFLICT (session_id)
DO UPDATE SET
    state = EXCLUDED.state,
    updated_at = NOW();
"""


# ---- GET STATE ----
GET_STATE = """
SELECT *
FROM working_memory
WHERE session_id = $1;
"""


# ---- DELETE ----
DELETE_STATE = """
DELETE FROM working_memory
WHERE session_id = $1;
"""