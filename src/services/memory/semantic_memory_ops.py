# ---- Imports ----
import logging


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- MemoryOps (Unified Memory Layer) ----
class SemanticMemoryOps:

    def __init__(self, db_client, queries):
        self.db = db_client
        self.q = queries

    # ---- INIT ----
    async def init(self) -> bool:
        logger.info("[MemoryOps] initializing...")

        try:
            await self.db.execute(self.q.CREATE_TABLE)
            await self.db.execute(self.q.CREATE_INDEX)
            await self.db.commit()
            return True

        except Exception as e:
            logger.exception(f"[MemoryOps] init failed: {e}")
            return False

    # ---- ADD MESSAGE ----
    async def add_message(
        self,
        user_id: str,
        role: str,
        content: str,
        embedding=None,
    ) -> bool:
        try:
            await self.db.execute(
                self.q.INSERT_MESSAGE,
                (user_id, role, content, embedding)
            )
            await self.db.commit()
            return True

        except Exception as e:
            logger.exception(f"[MemoryOps] add_message failed: {e}")
            return False

    # ---- USER HISTORY ----
    async def get_user_history(self, user_id: str):
        try:
            return await self.db.execute(
                self.q.GET_USER_HISTORY,
                (user_id,)
            )
        except Exception as e:
            logger.exception(f"[MemoryOps] get_user_history failed: {e}")
            return []

    # ---- STM (RECENT MEMORY) ----
    async def get_stm(self, user_id: str, limit: int = 10):
        try:
            return await self.db.execute(
                self.q.GET_STM,
                (user_id, limit),
                fetch=True
            )
        except Exception as e:
            logger.exception(f"[MemoryOps] get_stm failed: {e}")
            return []

    # ---- VECTOR SEARCH (semantic retrieval on same table) ----
    async def vector_search(self, user_id: str, embedding) -> list:
        try:
            return await self.db.execute(
                self.q.VECTOR_SEARCH,
                (user_id, embedding)
            )
        except Exception as e:
            logger.exception(f"[MemoryOps] vector_search failed: {e}")
            return []

    # ---- COUNT ----
    async def count(self) -> int:
        try:
            row = await self.db.execute_one(self.q.COUNT_ROWS)
            return row["total"] if row else 0
        except Exception as e:
            logger.exception(f"[MemoryOps] count failed: {e}")
            return 0