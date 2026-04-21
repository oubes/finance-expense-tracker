# ---- Imports ----
import logging


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- User Facts Use Case ----
class UserFactsUseCase:

    def __init__(self, db_client, queries):
        self.db = db_client
        self.q = queries

    # ---- INIT ----
    async def init(self) -> bool:
        logger.info("[User Facts Use Case] initializing...")

        try:
            table_exists = await self.db.execute_one(self.q.TABLE_EXISTS_SQL)

            if table_exists and table_exists.get("to_regclass"):
                logger.info("[User Facts Use Case] user_facts already initialized")
                return True

            async with self.db:
                await self.db.execute(self.q.CREATE_TABLE_SQL)
                await self.db.execute(self.q.CREATE_INDEX_SQL)

            logger.info("[User Facts Use Case] init success")
            return False

        except Exception as e:
            logger.exception("[User Facts Use Case] init failed")
            raise RuntimeError("Failed to initialize user_facts") from e

    # ---- HEALTH ----
    async def health(self):
        logger.info("[User Facts Use Case] health check start")

        try:
            table_exists = await self.db.execute_one(self.q.TABLE_EXISTS_SQL)

            if table_exists and table_exists.get("to_regclass"):
                logger.info("[User Facts Use Case] health check success")
                return True

            return False

        except Exception as e:
            logger.exception("[User Facts Use Case] health failed")
            raise RuntimeError("User facts health check failed") from e

    # ---- ADD ----
    async def upsert(self, data: tuple) -> None:
        logger.info("[User Facts Use Case] upsert (add or update) start")

        if not data:
            raise ValueError("data is empty")

        try:
            async with self.db:
                await self.db.execute(self.q.UPSERT_FACTS_SQL, data)

            logger.info("[User Facts Use Case] upsert success")

        except Exception as e:
            logger.exception("[User Facts Use Case] upsert failed")
            raise RuntimeError("Upsert user facts failed") from e

    async def update(self, data: tuple) -> None:
        logger.info("[User Facts Use Case] update start")

        if not data:
            raise ValueError("data is empty")

        try:
            async with self.db:
                await self.db.execute(self.q.UPDATE_FACTS_SQL, data)

            logger.info("[User Facts Use Case] update success")

        except Exception as e:
            logger.exception("[User Facts Use Case] update failed")
            raise RuntimeError("Update user facts failed") from e

    # ---- GET LATEST ----
    async def get_user_facts(self, user_id: str):
        logger.info("[User Facts Use Case] get_user_facts start")

        try:
            if not user_id:
                raise ValueError("user_id required")

            return await self.db.execute_one(
                self.q.GET_USER_FACTS_SQL,
                (user_id,)
            )

        except Exception:
            logger.exception("[User Facts Use Case] get_user_facts failed")
            return None

    # ---- GET HISTORY ----
    # get_history removed: only one row per user

    # ---- COUNT ----
    async def count(self) -> int:
        logger.info("[User Facts Use Case] count start")

        try:
            row = await self.db.execute_one(self.q.COUNT_ROWS_SQL)

            if not row:
                return 0

            if isinstance(row, dict):
                return list(row.values())[0]

            return row[0]

        except Exception as e:
            logger.exception("[User Facts Use Case] count failed")
            raise RuntimeError("User facts count failed") from e

    # ---- COUNT USER ----
    async def count_user(self, user_id: str) -> int:
        logger.info("[User Facts Use Case] count_user start")

        try:
            row = await self.db.execute_one(
                self.q.COUNT_BY_USER_SQL,
                (user_id,)
            )

            if not row:
                return 0

            if isinstance(row, dict):
                return list(row.values())[0]

            return row[0]

        except Exception as e:
            logger.exception("[User Facts Use Case] count_user failed")
            raise RuntimeError("User facts count_user failed") from e

    # ---- DELETE ALL ----
    async def delete_all(self) -> None:
        logger.info("[User Facts Use Case] delete_all start")

        try:
            async with self.db:
                await self.db.execute(self.q.DELETE_ALL_SQL)

            logger.info("[User Facts Use Case] delete_all success")

        except Exception as e:
            logger.exception("[User Facts Use Case] delete_all failed")
            raise RuntimeError("User facts delete_all failed") from e

    # ---- DROP TABLE ----
    async def drop_table(self) -> bool:
        logger.info("[User Facts Use Case] drop_table start")

        try:
            table_exists = await self.db.execute_one(self.q.TABLE_EXISTS_SQL)

            if not table_exists or not table_exists.get("to_regclass"):
                logger.info("[User Facts Use Case] user_facts does not exist")
                return False

            async with self.db:
                await self.db.execute(self.q.DROP_TABLE_SQL)

            logger.info("[User Facts Use Case] drop_table success")
            return True

        except Exception as e:
            logger.exception("[User Facts Use Case] drop_table failed")
            raise RuntimeError("User facts drop_table failed") from e