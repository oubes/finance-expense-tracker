CREATE_CHUNKS_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS rag_cv_chunks (
        id SERIAL PRIMARY KEY,
        doc_name TEXT,
        section TEXT,
        chunk_index INT,
        content TEXT,
        embedding VECTOR({dim})
    )
"""


INSERT_CHUNK_SQL = """
    INSERT INTO rag_cv_chunks
    (doc_name, section, chunk_index, content, embedding)
    VALUES (%s, %s, %s, %s, %s)
"""


SEARCH_CHUNKS_SQL = """
    SELECT section, content, 1 - (embedding <=> %s::vector) AS cosine_sim
    FROM rag_cv_chunks
    WHERE doc_name = %s
    ORDER BY embedding <=> %s::vector
    LIMIT %s
"""


DELETE_CHUNKS_SQL = """
    DELETE FROM rag_cv_chunks;
"""


COUNT_CHUNKS_SQL = """
    SELECT COUNT(*) FROM rag_cv_chunks;
"""


PREVIEW_CHUNKS_SQL = """
    SELECT doc_name, section, content
    FROM rag_cv_chunks
    LIMIT %s
"""

KEYWORD_SEARCH_CHUNKS_SQL = """
    SELECT 
        section,
        content,
        ts_rank_cd(
            to_tsvector('english', content),
            plainto_tsquery('english', %s)
        ) AS score
    FROM rag_cv_chunks
    WHERE doc_name = %s
      AND to_tsvector('english', content) @@ plainto_tsquery('english', %s)
    ORDER BY score DESC
    LIMIT %s;
"""