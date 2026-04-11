# ---- Imports ----
import logging


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Session State Ops ----
class SessionStateOps:

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
            logger.exception(f"[SessionStateOps] init failed: {e}")
            return False

    # ---- SET STATE ----
    async def set_state(self, data: tuple) -> bool:
        try:
            await self.db.execute(self.queries.SET_STATE, data)
            await self.db.commit()
            return True
        except Exception as e:
            logger.exception(f"[SessionStateOps] set_state failed: {e}")
            return False

    # ---- GET STATE ----
    async def get_state(self, session_id: str):
        try:
            return await self.db.execute_one(
                self.queries.GET_STATE,
                (session_id,)
            )
        except Exception as e:
            logger.exception(f"[SessionStateOps] get_state failed: {e}")
            return None

    # ---- DELETE STATE ----
    async def delete_state(self, session_id: str) -> bool:
        try:
            await self.db.execute(
                self.queries.DELETE_STATE,
                (session_id,)
            )
            await self.db.commit()
            return True
        except Exception as e:
            logger.exception(f"[SessionStateOps] delete_state failed: {e}")
            return False