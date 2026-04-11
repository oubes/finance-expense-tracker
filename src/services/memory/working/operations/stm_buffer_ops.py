# ---- Imports ----
import logging


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- STM Buffer Ops ----
class STMBufferOps:

    def __init__(self, db_client, queries):
        self.db = db_client
        self.queries = queries

    # ---- INIT ----
    async def init(self) -> bool:
        try:
            await self.db.execute(self.queries.CREATE_TABLE)
            await self.db.execute(self.queries.CREATE_INDEX)
            await self.db.commit()
            return True
        except Exception as e:
            logger.exception(f"[STMBufferOps] init failed: {e}")
            return False

    # ---- PUSH ----
    async def push(self, data: tuple) -> bool:
        try:
            await self.db.execute(self.queries.PUSH, data)
            await self.db.commit()
            return True
        except Exception as e:
            logger.exception(f"[STMBufferOps] push failed: {e}")
            return False

    # ---- POP ----
    async def pop(self, session_id: str):
        try:
            return await self.db.execute_one(
                self.queries.POP,
                (session_id,)
            )
        except Exception as e:
            logger.exception(f"[STMBufferOps] pop failed: {e}")
            return None

    # ---- GET ALL ----
    async def get_all(self, session_id: str):
        try:
            return await self.db.execute(
                self.queries.GET_ALL,
                (session_id,)
            )
        except Exception as e:
            logger.exception(f"[STMBufferOps] get_all failed: {e}")
            return []

    # ---- CLEAR ----
    async def clear(self, session_id: str) -> bool:
        try:
            await self.db.execute(
                self.queries.CLEAR,
                (session_id,)
            )
            await self.db.commit()
            return True
        except Exception as e:
            logger.exception(f"[STMBufferOps] clear failed: {e}")
            return False