import logging
from pgvector.psycopg import register_vector_async

logger = logging.getLogger(__name__)

# ---- Vector Extension Handler ----
class VectorExtension:
    # ---- Initialization ----
    def __init__(self, conn):
        self.conn = conn
        self.enabled = False

    # ---- Enable pgvector Extension ----
    async def enable(self):
        logger.info("Enabling pgvector extension...")

        # ---- Validate Connection ----
        if not self.conn:
            logger.error("No database connection provided for pgvector.")
            self.enabled = False
            return False

        try:
            # ---- Register Extension ----
            await register_vector_async(self.conn)

            # ---- Mark as Enabled ----
            self.enabled = True
            logger.info("pgvector extension enabled successfully.")
            return True

        except Exception:
            # ---- Failure Handling ----
            self.enabled = False
            logger.exception("Failed to enable pgvector extension.")
            return False

    # ---- Status Check ----
    def is_enabled(self):
        # ---- Debug State ----
        if not self.enabled:
            logger.debug("pgvector extension is not enabled.")
        return self.enabled