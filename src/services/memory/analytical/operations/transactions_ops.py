# ---- Imports ----
import logging


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Transactions Ops (Memory Event Log) ----
class TransactionsOps:

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
            logger.exception(f"[TransactionsOps] init failed: {e}")
            return False

    # ---- LOG EVENT ----
    async def log_event(self, data: tuple) -> bool:
        try:
            await self.db.execute(self.queries.INSERT_EVENT, data)
            await self.db.commit()
            return True

        except Exception as e:
            logger.exception(f"[TransactionsOps] log_event failed: {e}")
            return False

    # ---- GET USER EVENTS ----
    async def get_user_events(self, user_id: str):
        try:
            return await self.db.execute(
                self.queries.GET_USER_EVENTS,
                (user_id,)
            )
        except Exception as e:
            logger.exception(f"[TransactionsOps] get_user_events failed: {e}")
            return []

    # ---- GET DOMAIN EVENTS ----
    async def get_by_domain(self, user_id: str, domain: str):
        try:
            return await self.db.execute(
                self.queries.GET_BY_DOMAIN,
                (user_id, domain)
            )
        except Exception as e:
            logger.exception(f"[TransactionsOps] get_by_domain failed: {e}")
            return []

    # ---- COUNT ----
    async def count(self) -> int:
        try:
            row = await self.db.execute_one(self.queries.COUNT_ROWS)
            return row["total"] if row else 0

        except Exception as e:
            logger.exception(f"[TransactionsOps] count failed: {e}")
            return 0