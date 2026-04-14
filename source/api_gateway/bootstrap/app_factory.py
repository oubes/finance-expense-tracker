# ---- Imports ----
import logging
from fastapi import FastAPI

from source.api_gateway.bootstrap.lifespan import lifespan
from source.api_gateway.bootstrap.middleware import register_middleware
from source.api_gateway.bootstrap.router import register_routes


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Application Factory ----
def create_app() -> FastAPI:
    logger.info("[APP_FACTORY] initializing FastAPI application")

    try:
        app = FastAPI(lifespan=lifespan)
        logger.info("[APP_FACTORY] FastAPI instance created successfully")

        # ---- Middleware Registration ----
        logger.info("[APP_FACTORY] registering middleware")
        try:
            register_middleware(app)
            logger.info("[APP_FACTORY] middleware registration SUCCESS")
        except Exception:
            logger.exception("[APP_FACTORY] middleware registration FAILED")
            raise

        # ---- Routes Registration ----
        logger.info("[APP_FACTORY] registering routes")
        try:
            register_routes(app)
            logger.info("[APP_FACTORY] routes registration SUCCESS")
        except Exception:
            logger.exception("[APP_FACTORY] routes registration FAILED")
            raise

        logger.info("[APP_FACTORY] application factory completed successfully")
        return app

    except Exception:
        logger.exception("[APP_FACTORY] critical failure during app creation")
        raise