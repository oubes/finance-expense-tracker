# ---- Imports ----
import logging


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- User Facts Operations ----
class UserFactsOps:

    # ---- Constructor ----
    def __init__(self, db_client, queries):
        self.db = db_client
        self.queries = queries

    # ---- INIT ----
    async def init(self) -> bool:
        logger.info("[UserFactsOps] initializing table...")

        try:
            await self.db.execute(self.queries.CREATE_TABLE)
            await self.db.execute(self.queries.CREATE_INDEX)
            await self.db.commit()

            return True

        except Exception as e:
            logger.exception(f"[UserFactsOps] init failed: {e}")
            return False

    # ---- RETRIEVE ----
    async def get(self, user_id: str) -> dict | None:
        return await self.db.execute_one(self.queries.GET_BY_USER_ID, (user_id,))

    # ---- ADD ----
    async def add(self, data: tuple) -> bool:
        try:
            await self.db.execute(self.queries.INSERT_FACTS, data)
            await self.db.commit()
            return True
        except Exception as e:
            logger.exception(f"[UserFactsOps] add failed: {e}")
            return False

    # ---- UPDATE ----
    async def update(self, data: tuple) -> bool:
        try:
            await self.db.execute(self.queries.UPDATE_FACTS, data)
            await self.db.commit()
            return True
        except Exception as e:
            logger.exception(f"[UserFactsOps] update failed: {e}")
            return False

    # ---- DELETE ----
    async def delete(self, user_id: str) -> bool:
        try:
            await self.db.execute(self.queries.DELETE_FACTS, (user_id,))
            await self.db.commit()
            return True
        except Exception as e:
            logger.exception(f"[UserFactsOps] delete failed: {e}")
            return False

    # ---- COUNT ----
    async def count(self) -> int:
        try:
            row = await self.db.execute_one(self.queries.COUNT_ROWS)
            return row["total"] if row else 0
        except Exception as e:
            logger.exception(f"[UserFactsOps] count failed: {e}")
            return 0