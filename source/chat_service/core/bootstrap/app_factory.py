# ---------- imports ----------

import logging
from fastapi import FastAPI

from source.ingestion_service.core.bootstrap.lifespan import lifespan
from source.ingestion_service.api.router_registry import register_routes



# ---------- logger ----------

logger = logging.getLogger(__name__)


# ---------- app factory ----------

def create_app() -> FastAPI:
    logger.info("[APP_FACTORY] initializing FastAPI application")

    try:
        app = FastAPI(lifespan=lifespan)

        logger.info("[APP_FACTORY] registering observability middleware")

        logger.info("[APP_FACTORY] registering exception handlers")

        logger.info("[APP_FACTORY] registering middleware stack")

        logger.info("[APP_FACTORY] registering routes")
        register_routes(app)

        logger.info("[APP_FACTORY] application factory completed successfully")

        return app

    except Exception:
        logger.exception("[APP_FACTORY] critical failure during app creation")
        raise