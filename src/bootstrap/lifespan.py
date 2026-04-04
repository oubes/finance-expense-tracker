from contextlib import asynccontextmanager
from fastapi import FastAPI
# from rate_limit.middleware import limiter
from src.infrastructure.vector_db.core.db_client import PostgresVectorClient
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    try:
        # await limiter.init()
        
        logger.info("App is starting up...")
        yield
        
    except Exception:
        logger.exception("Startup failed")
        raise
        
    finally:
        # if hasattr(app.state, "db_client"):
            # await db_client.close()
        
        logger.info("App is shutting down...")