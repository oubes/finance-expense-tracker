from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class DBExecutor:
    def __init__(self, db_connect):
        self.db = db_connect

    async def execute(self, query, params=None, fetch: bool = False):
        try:
            async with self.db.conn.cursor() as cur:
                await cur.execute(query, params or ())

                if fetch:
                    result = await cur.fetchall()
                    logger.debug("Query executed successfully (fetchall).")
                    return result

                logger.debug("Query executed successfully (no fetch).")
                return None

        except Exception:
            logger.exception("Execute failed.")
            return None

    async def execute_one(self, query, params=None):
        try:
            async with self.db.conn.cursor() as cur:
                await cur.execute(query, params or ())
                result = await cur.fetchone()

                logger.debug("Query executed successfully (fetchone).")
                return result

        except Exception:
            logger.exception("Execute one failed.")
            return None

    async def commit(self):
        try:
            await self.db.conn.commit()
            logger.debug("Transaction committed successfully.")

        except Exception:
            logger.exception("Commit failed.")