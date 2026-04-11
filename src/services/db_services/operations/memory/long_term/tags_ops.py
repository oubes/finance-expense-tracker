# ---- Imports ----
import logging


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Tags Ops ----
class TagsOps:

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
            logger.exception(f"[TagsOps] init failed: {e}")
            return False

    # ---- ADD TAG ----
    async def add_tag(self, data: tuple) -> bool:
        try:
            await self.db.execute(self.queries.INSERT_TAG, data)
            await self.db.commit()
            return True

        except Exception as e:
            logger.exception(f"[TagsOps] add_tag failed: {e}")
            return False

    # ---- GET TAGS ----
    async def get_tags(self, user_id: str):
        try:
            return await self.db.execute(
                self.queries.GET_TAGS_BY_USER,
                (user_id,)
            )
        except Exception as e:
            logger.exception(f"[TagsOps] get_tags failed: {e}")
            return []

    # ---- DELETE TAGS ----
    async def delete_tags(self, user_id: str) -> bool:
        try:
            await self.db.execute(
                self.queries.DELETE_TAGS,
                (user_id,)
            )
            await self.db.commit()
            return True

        except Exception as e:
            logger.exception(f"[TagsOps] delete_tags failed: {e}")
            return False

    # ---- COUNT ----
    async def count(self) -> int:
        try:
            row = await self.db.execute_one(self.queries.COUNT_ROWS)
            return row["total"] if row else 0

        except Exception as e:
            logger.exception(f"[TagsOps] count failed: {e}")
            return 0