# ---- Imports ----
import logging

# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Transactions Use Case ----
class TransactionsUseCase:

    def __init__(self, db_client, queries):
        self.db = db_client
        self.queries = queries

    # ---- INIT ----
    async def init(self) -> bool:
        try:
            await self.db.execute(self.queries.CREATE_TABLE)
            await self.db.execute(self.queries.CREATE_INDEX)
            await self.db.commit()

            logger.info("[Transactions Use Case] init success")
            return True

        except Exception as e:
            logger.exception(f"[Transactions Use Case] init failed: {e}")
            return False

    # ---- INSERT EVENT ----
    async def log_event(self, data: tuple) -> bool:
        try:
            # expected tuple:
            # (user_id, product, category, amount, quantity, currency, note, raw_input)

            await self.db.execute(self.queries.INSERT_EVENT, data)
            await self.db.commit()

            logger.info("[Transactions Use Case] log_event success")
            return True

        except Exception as e:
            logger.exception(f"[Transactions Use Case] log_event failed: {e}")
            return False

    # ---- GET USER EVENTS ----
    async def get_user_events(self, user_id: str):
        try:
            result = await self.db.execute(
                self.queries.GET_USER_EVENTS,
                (user_id,)
            )

            logger.info("[Transactions Use Case] get_user_events success")
            return result

        except Exception as e:
            logger.exception(f"[Transactions Use Case] get_user_events failed: {e}")
            return []

    # ---- GET BY CATEGORY ----
    async def get_by_category(self, user_id: str, category: str):
        try:
            result = await self.db.execute(
                self.queries.GET_BY_CATEGORY,
                (user_id, category)
            )

            logger.info("[Transactions Use Case] get_by_category success")
            return result

        except Exception as e:
            logger.exception(f"[Transactions Use Case] get_by_category failed: {e}")
            return []

    # ---- COUNT ----
    async def count(self) -> int:
        try:
            row = await self.db.execute_one(self.queries.COUNT_ROWS)

            result = row["total"] if row else 0

            logger.info(f"[Transactions Use Case] count success: {result}")
            return result

        except Exception as e:
            logger.exception(f"[Transactions Use Case] count failed: {e}")
            return 0