from abc import ABC, abstractmethod
import logging
from pgvector.psycopg import register_vector_async

logger = logging.getLogger(__name__)

class VectorExtension:
    def __init__(self, conn):
        self.conn = conn
        self.enabled = False

    async def enable(self):
        logger.info("Enabling pgvector extension...")

        if not self.conn:
            logger.error("No database connection provided for pgvector.")
            self.enabled = False
            return False

        try:
            await register_vector_async(self.conn)

            self.enabled = True
            logger.info("pgvector extension enabled successfully.")
            return True

        except Exception:
            self.enabled = False
            logger.exception("Failed to enable pgvector extension.")
            return False

    def is_enabled(self):
        if not self.enabled:
            logger.debug("pgvector extension is not enabled.")
        return self.enabled