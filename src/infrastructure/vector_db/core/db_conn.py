# ---- Imports ----
import logging
from psycopg import AsyncConnection
from src.core.config.settings import AppSettings

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)


# ---- DB Connection Class ----
class DBConnect:

    # ---- Constructor ----
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.conn: AsyncConnection | None = None

    # ---- Connect to Database ----
    async def connect(self):
        logger.info("Attempting to connect to database...")

        try:
            self.conn = await AsyncConnection.connect(
                self.settings.database.full_url # type: ignore
            )

            logger.info("Database connected successfully.")
            return True

        except Exception:
            logger.exception("Database connection failed.")
            self.conn = None
            return False

    # ---- Health Check ----
    async def is_alive(self):
        if not self.conn:
            logger.warning("Database connection is not initialized.")
            return False

        try:
            async with self.conn.cursor() as cur:
                await cur.execute("SELECT 1;")

            logger.debug("Database health check passed.")
            return True

        except Exception:
            logger.exception("Database health check failed.")
            return False

    # ---- Close Connection ----
    async def close(self):
        if not self.conn:
            logger.warning("Attempted to close a non-existent DB connection.")
            return

        try:
            await self.conn.close()
            logger.info("Database connection closed successfully.")

        except Exception:
            logger.exception("Failed to close database connection.")