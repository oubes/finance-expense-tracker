# ---- Vector Queries ----


# ---- UPSERT VECTOR META ----
UPSERT_VECTOR = """
INSERT INTO memory_vectors (
    user_id,
    vector_id,
    doc_id,
    metadata
)
VALUES ($1,$2,$3,$4)
ON CONFLICT (vector_id)
DO UPDATE SET
    metadata = EXCLUDED.metadata;
"""


# ---- GET BY USER ----
GET_BY_USER = """
SELECT *
FROM memory_vectors
WHERE user_id = $1;
"""


# ---- DELETE ----
DELETE_BY_DOC = """
DELETE FROM memory_vectors
WHERE doc_id = $1;
"""


# ---- COUNT ----
COUNT_ROWS = """
SELECT COUNT(*) AS total
FROM memory_vectors;
"""