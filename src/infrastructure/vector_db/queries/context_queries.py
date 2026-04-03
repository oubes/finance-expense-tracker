CREATE_CONTEXT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS rag_context_memory (
    id SERIAL PRIMARY KEY,
    session_id TEXT,
    role TEXT,
    content TEXT,
    embedding VECTOR({dim}),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


INSERT_CONTEXT_SQL = """
INSERT INTO rag_context_memory
(session_id, role, content, embedding)
VALUES (%s, %s, %s, %s)
"""


SEARCH_CONTEXT_SQL = """
SELECT 
    role,
    content,
    1 - (embedding <=> %s::vector) AS cosine_sim
FROM rag_context_memory
WHERE session_id = %s
ORDER BY embedding <=> %s::vector
LIMIT %s
"""


GET_RECENT_CONTEXT_SQL = """
SELECT role, content
FROM rag_context_memory
WHERE session_id = %s
ORDER BY created_at DESC
LIMIT %s
"""


DELETE_CONTEXT_BY_SESSION_SQL = """
DELETE FROM rag_context_memory
WHERE session_id = %s
"""


COUNT_CONTEXT_SQL = """
SELECT COUNT(*) 
FROM rag_context_memory
WHERE session_id = %s
"""