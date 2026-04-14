# ---- Imports ----
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)


# ---- Application Lifespan ----
@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("[LIFESPAN] initializing application lifespan")

    try:
        # ---- Startup ----
        logger.info("[LIFESPAN] startup initiated")

        yield

        logger.info("[LIFESPAN] application running")

    except Exception:
        logger.exception("[LIFESPAN] startup failure")
        raise

    finally:
        # ---- Shutdown ----
        logger.info("[LIFESPAN] shutdown initiated")
        logger.info("[LIFESPAN] application shutdown complete")