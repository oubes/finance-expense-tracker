# ---- Imports ----
import logging


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Analytics Ops ----
class AnalyticsOps:

    # ---- Constructor ----
    def __init__(self, db_client, queries):
        self.db = db_client
        self.q = queries

    # ---- MONTHLY SPENDING ----
    async def monthly_spending(self, user_id: str) -> list[dict] | None:
        try:
            return await self.db.execute(self.q.MONTHLY_SPENDING, (user_id,))
        except Exception as e:
            logger.exception(f"[AnalyticsOps] monthly_spending failed: {e}")
            return None

    # ---- CATEGORY BREAKDOWN ----
    async def category_breakdown(self, user_id: str) -> list[dict] | None:
        try:
            return await self.db.execute(self.q.CATEGORY_BREAKDOWN, (user_id,))
        except Exception as e:
            logger.exception(f"[AnalyticsOps] category_breakdown failed: {e}")
            return None

    # ---- INCOME VS EXPENSE ----
    async def income_vs_expense(self, user_id: str) -> list[dict] | None:
        try:
            return await self.db.execute(self.q.INCOME_VS_EXPENSE, (user_id,))
        except Exception as e:
            logger.exception(f"[AnalyticsOps] income_vs_expense failed: {e}")
            return None

    # ---- AVERAGE SPEND ----
    async def average_spend(self, user_id: str) -> float | None:
        try:
            row = await self.db.execute_one(self.q.AVERAGE_SPEND, (user_id,))
            return row["avg_spend"] if row else None
        except Exception as e:
            logger.exception(f"[AnalyticsOps] average_spend failed: {e}")
            return None