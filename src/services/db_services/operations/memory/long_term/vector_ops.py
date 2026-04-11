# ---- Imports ----
import logging


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Vector Ops (External System Wrapper) ----
class VectorOps:

    def __init__(self, db_client, queries):
        self.db = db_client
        self.queries = queries

    # ---- INIT ----
    async def init(self) -> bool:
        # assumes external system already exists
        return True

    # ---- UPSERT ----
    async def upsert(self, data: tuple) -> bool:
        try:
            await self.db.execute(self.queries.UPSERT_VECTOR, data)
            await self.db.commit()
            return True
        except Exception as e:
            logger.exception(f"[VectorOps] upsert failed: {e}")
            return False

    # ---- GET BY USER ----
    async def get_by_user(self, user_id: str):
        try:
            return await self.db.execute(
                self.queries.GET_BY_USER,
                (user_id,)
            )
        except Exception as e:
            logger.exception(f"[VectorOps] get_by_user failed: {e}")
            return []

    # ---- DELETE ----
    async def delete_by_doc(self, doc_id: str) -> bool:
        try:
            await self.db.execute(
                self.queries.DELETE_BY_DOC,
                (doc_id,)
            )
            await self.db.commit()
            return True
        except Exception as e:
            logger.exception(f"[VectorOps] delete_by_doc failed: {e}")
            return False