# ---- Imports ----
import logging


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Conversation Ops ----
class ConversationOps:

    def __init__(self, db_client, queries):
        self.db = db_client
        self.queries = queries

    # ---- INIT ----
    async def init(self) -> bool:
        logger.info("[ConversationOps] initializing...")

        try:
            await self.db.execute(self.queries.CREATE_TABLE)
            await self.db.execute(self.queries.CREATE_INDEX)
            await self.db.commit()
            return True

        except Exception as e:
            logger.exception(f"[ConversationOps] init failed: {e}")
            return False

    # ---- ADD MESSAGE ----
    async def add(self, data: tuple) -> bool:
        try:
            await self.db.execute(self.queries.INSERT_MESSAGE, data)
            await self.db.commit()
            return True

        except Exception as e:
            logger.exception(f"[ConversationOps] add failed: {e}")
            return False

    # ---- GET HISTORY ----
    async def get_history(self, session_id: str):
        return await self.db.execute(
            self.queries.GET_HISTORY,
            (session_id,)
        )

    # ---- GET USER ACTIVITY ----
    async def get_user_recent(self, user_id: str):
        return await self.db.execute(
            self.queries.GET_USER_RECENT,
            (user_id,)
        )

    # ---- DELETE SESSION ----
    async def delete_session(self, session_id: str) -> bool:
        try:
            await self.db.execute(
                self.queries.DELETE_SESSION,
                (session_id,)
            )
            await self.db.commit()
            return True

        except Exception as e:
            logger.exception(f"[ConversationOps] delete failed: {e}")
            return False

    # ---- COUNT ----
    async def count(self) -> int:
        try:
            row = await self.db.execute_one(self.queries.COUNT_ROWS)
            return row["total"] if row else 0

        except Exception as e:
            logger.exception(f"[ConversationOps] count failed: {e}")
            return 0