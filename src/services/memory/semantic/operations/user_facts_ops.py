# ---- Imports ----
import logging


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- User Facts Ops (Versioned / Append-only) ----
class UserFactsOps:

    def __init__(self, db_client, queries):
        self.db = db_client
        self.queries = queries

    # ---- INIT ----
    async def init(self) -> bool:
        logger.info("[UserFactsOps] initializing versioned table...")

        try:
            await self.db.execute(self.queries.CREATE_TABLE)
            await self.db.execute(self.queries.CREATE_INDEX)
            await self.db.commit()
            return True

        except Exception as e:
            logger.exception(f"[UserFactsOps] init failed: {e}")
            return False

    # ---- ADD (NEW VERSION) ----
    async def add(self, data: tuple) -> bool:
        """
        Inserts a new version of user facts (append-only).
        """
        try:
            await self.db.execute(self.queries.INSERT_FACTS, data)
            await self.db.commit()
            return True

        except Exception as e:
            logger.exception(f"[UserFactsOps] add failed: {e}")
            return False

    # ---- GET LATEST ----
    async def get_latest(self, user_id: str):
        """
        Returns most recent fact snapshot for a user.
        """
        return await self.db.execute_one(
            self.queries.GET_LATEST_BY_USER_ID,
            (user_id,)
        )

    # ---- GET HISTORY ----
    async def get_history(self, user_id: str):
        """
        Returns full fact timeline for a user.
        """
        return await self.db.execute(
            self.queries.GET_HISTORY_BY_USER_ID,
            (user_id,)
        )

    # ---- COUNT GLOBAL ----
    async def count(self) -> int:
        try:
            row = await self.db.execute_one(self.queries.COUNT_ROWS)
            return row["total"] if row else 0

        except Exception as e:
            logger.exception(f"[UserFactsOps] count failed: {e}")
            return 0

    # ---- COUNT PER USER ----
    async def count_user(self, user_id: str) -> int:
        try:
            row = await self.db.execute_one(
                self.queries.COUNT_BY_USER,
                (user_id,)
            )
            return row["total"] if row else 0

        except Exception as e:
            logger.exception(f"[UserFactsOps] count_user failed: {e}")
            return 0