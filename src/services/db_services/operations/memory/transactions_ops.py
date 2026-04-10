# ---- Imports ----
import logging


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Transactions Ops ----
class TransactionsOps:

    # ---- Constructor ----
    def __init__(self, db_client, queries):
        self.db = db_client
        self.q = queries

    # ---- INIT ----
    async def init(self) -> bool:
        try:
            await self.db.execute(self.q.CREATE_TABLE)
            await self.db.execute(self.q.CREATE_INDEX)
            await self.db.commit()
            return True
        except Exception as e:
            logger.exception(f"[TransactionsOps] init failed: {e}")
            return False

    # ---- ADD ----
    async def add(self, data: tuple) -> bool:
        try:
            await self.db.execute(self.q.INSERT_TRANSACTION, data)
            await self.db.commit()
            return True
        except Exception as e:
            logger.exception(f"[TransactionsOps] add failed: {e}")
            return False

    # ---- UPDATE ----
    async def update(self, data: tuple) -> bool:
        try:
            await self.db.execute(self.q.UPDATE_TRANSACTION, data)
            await self.db.commit()
            return True
        except Exception as e:
            logger.exception(f"[TransactionsOps] update failed: {e}")
            return False

    # ---- DELETE ----
    async def delete(self, transaction_id: int, user_id: str) -> bool:
        try:
            await self.db.execute(
                self.q.DELETE_TRANSACTION,
                (transaction_id, user_id)
            )
            await self.db.commit()
            return True
        except Exception as e:
            logger.exception(f"[TransactionsOps] delete failed: {e}")
            return False

    # ---- FETCH ----
    async def fetch_by_user(self, user_id: str) -> list[dict] | None:
        try:
            return await self.db.execute(self.q.GET_BY_USER, (user_id,))
        except Exception as e:
            logger.exception(f"[TransactionsOps] fetch failed: {e}")
            return None

    # ---- COUNT ----
    async def count(self, user_id: str) -> int:
        try:
            row = await self.db.execute_one(self.q.COUNT_BY_USER, (user_id,))
            return row["total"] if row else 0
        except Exception as e:
            logger.exception(f"[TransactionsOps] count failed: {e}")
            return 0