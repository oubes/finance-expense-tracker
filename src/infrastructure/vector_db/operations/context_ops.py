# ---- Imports ----
import logging

from infrastructure.vector_db.queries.context_queries import (
    CREATE_CONTEXT_TABLE_SQL,
    INSERT_CONTEXT_SQL,
    SEARCH_CONTEXT_SQL,
    GET_RECENT_CONTEXT_SQL,
    DELETE_CONTEXT_BY_SESSION_SQL,
    COUNT_CONTEXT_SQL,
)

logger = logging.getLogger(__name__)


# ---- Initialize Context Table ----
async def init_context_table(client, dim: int):
    try:
        sql = CREATE_CONTEXT_TABLE_SQL.format(dim=dim)
        await client.execute(sql)
        await client.commit()
        logger.info("Context table initialized.")
    except Exception:
        logger.exception("init_context_table failed.")
        raise


# ---- Insert Context ----
async def insert_context(client, session_id, role, content, embedding):
    try:
        await client.execute(
            INSERT_CONTEXT_SQL,
            (session_id, role, content, embedding)
        )
        await client.commit()
    except Exception:
        logger.exception("insert_context failed.")
        raise


# ---- Search Context ----
async def search_context(client, query_embedding, session_id, limit=5):
    try:
        rows = await client.execute(
            SEARCH_CONTEXT_SQL,
            (
                query_embedding,
                session_id,
                query_embedding,
                limit,
            ),
            fetch=True
        )
        return rows or []
    except Exception:
        logger.exception("search_context failed.")
        return []


# ---- Get Recent Context ----
async def get_recent_context(client, session_id, limit=10):
    try:
        rows = await client.execute(
            GET_RECENT_CONTEXT_SQL,
            (session_id, limit),
            fetch=True
        )
        return rows or []
    except Exception:
        logger.exception("get_recent_context failed.")
        return []


# ---- Delete Context By Session ----
async def delete_context_session(client, session_id):
    try:
        await client.execute(
            DELETE_CONTEXT_BY_SESSION_SQL,
            (session_id,)
        )
        await client.commit()
    except Exception:
        logger.exception("delete_context_session failed.")
        raise


# ---- Count Context ----
async def count_context(client, session_id):
    try:
        result = await client.execute_one(
            COUNT_CONTEXT_SQL,
            (session_id,)
        )
        return result[0] if result else 0
    except Exception:
        logger.exception("count_context failed.")
        return 0