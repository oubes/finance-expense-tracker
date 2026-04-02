from abc import ABC, abstractmethod
import logging
import psycopg
from psycopg import AsyncConnection
from src.core.config.loader import load_settings
from src.core.config.settings import AppSettings

settings: AppSettings = load_settings()
logger = logging.getLogger(__name__)

class DBConnect:
    def __init__(self):
        self.conn: AsyncConnection | None = None

    async def connect(self):
        logger.info("Attempting to connect to database...")
        
        try:
            self.conn = await AsyncConnection.connect(settings.database.full_url) # type: ignore
            
            logger.info("Database connected successfully.")
            return True

        except Exception:
            logger.exception("Database connection failed.")
            self.conn = None
            return False

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

    async def close(self):
        if not self.conn:
            logger.warning("Attempted to close a non-existent DB connection.")
            return

        try:
            await self.conn.close()
            logger.info("Database connection closed successfully.")

        except Exception:
            logger.exception("Failed to close database connection.")