# ---- Imports ----
import logging


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Analytics Ops (Behavioral Signals) ----
class AnalyticsOps:

    def __init__(self, db_client, queries):
        self.db = db_client
        self.queries = queries

    # ---- INIT ----
    async def init(self) -> bool:
        """
        No table creation required (read-only analytical layer).
        """
        return True

    # ---- USER ACTIVITY ----
    async def get_user_activity(self, user_id: str):
        try:
            return await self.db.execute_one(
                self.queries.GET_USER_ACTIVITY,
                (user_id,)
            )
        except Exception as e:
            logger.exception(f"[AnalyticsOps] activity failed: {e}")
            return None

    # ---- DOMAIN DISTRIBUTION ----
    async def get_domain_distribution(self, user_id: str):
        try:
            return await self.db.execute(
                self.queries.GET_DOMAIN_DISTRIBUTION,
                (user_id,)
            )
        except Exception as e:
            logger.exception(f"[AnalyticsOps] domain dist failed: {e}")
            return []

    # ---- TAG SIGNALS ----
    async def get_tag_signals(self, user_id: str):
        try:
            return await self.db.execute(
                self.queries.GET_TAG_SIGNALS,
                (user_id,)
            )
        except Exception as e:
            logger.exception(f"[AnalyticsOps] tag signals failed: {e}")
            return []

    # ---- CONVERSATION INTENSITY ----
    async def get_conversation_intensity(self, user_id: str):
        try:
            return await self.db.execute(
                self.queries.GET_CONVERSATION_INTENSITY,
                (user_id,)
            )
        except Exception as e:
            logger.exception(f"[AnalyticsOps] intensity failed: {e}")
            return []

    # ---- MEMORY GROWTH ----
    async def get_memory_growth(self, user_id: str):
        try:
            return await self.db.execute(
                self.queries.GET_MEMORY_GROWTH,
                (user_id,)
            )
        except Exception as e:
            logger.exception(f"[AnalyticsOps] growth failed: {e}")
            return []