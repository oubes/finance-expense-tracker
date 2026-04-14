# ---------- imports ----------

import logging
from fastapi import FastAPI

from source.api_gateway.core.bootstrap.lifespan import lifespan
from source.api_gateway.core.middleware import register_middleware
from source.api_gateway.api.router_registry import register_routes

from source.api_gateway.core.errors.exceptions import BaseAPIException
from source.api_gateway.core.errors.error_handlers import base_exception_handler, generic_exception_handler


# ---------- logger ----------

logger = logging.getLogger(__name__)


# ---------- app factory ----------

def create_app() -> FastAPI:
    logger.info("[APP_FACTORY] initializing FastAPI application")

    try:
        app = FastAPI(lifespan=lifespan)

        logger.info("[APP_FACTORY] registering exception handlers")
        app.add_exception_handler(BaseAPIException, base_exception_handler)
        app.add_exception_handler(Exception, generic_exception_handler)

        logger.info("[APP_FACTORY] registering middleware")
        register_middleware(app)

        logger.info("[APP_FACTORY] registering routes")
        register_routes(app)

        logger.info("[APP_FACTORY] application factory completed successfully")

        return app

    except Exception:
        logger.exception("[APP_FACTORY] critical failure during app creation")
        raise