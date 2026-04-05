# ---- Imports ----
from contextlib import asynccontextmanager
from fastapi import FastAPI
# from rate_limit.middleware import limiter
from src.infrastructure.vector_db.core.db_client import PostgresVectorClient
import logging

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)


# ---- Application Lifespan ----
@asynccontextmanager
async def lifespan(app: FastAPI):
    
    try:
        # await limiter.init()
        
        # ---- Startup ----
        logger.info("App is starting up...")
        yield
        
    except Exception:
        logger.exception("Startup failed")
        raise
        
    finally:
        # ---- Shutdown ----
        # if hasattr(app.state, "db_client"):
            # await db_client.close()
        
        logger.info("App is shutting down...")