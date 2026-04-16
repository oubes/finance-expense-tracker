# ---------- imports ----------

import logging
from fastapi import FastAPI

from source.infra_service.core.bootstrap.lifespan import lifespan
from source.infra_service.api.router_registry import register_routes
import asyncio


# ---------- logger ----------

logger = logging.getLogger(__name__)


# ---------- app factory ----------

def create_app() -> FastAPI:
    logger.info("[APP_FACTORY] initializing FastAPI application")
    
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        app = FastAPI(lifespan=lifespan)

        register_routes(app)

        logger.info("[APP_FACTORY] application factory completed successfully")

        return app

    except Exception:
        logger.exception("[APP_FACTORY] critical failure during app creation")
        raise