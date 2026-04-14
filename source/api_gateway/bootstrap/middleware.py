# ---- Imports ----
import time
import logging
from fastapi import Request

# ---- Logger Initialization ----
logger = logging.getLogger(__name__)


# ---- Middleware Registration ----
def register_middleware(app):

    logger.info("[MIDDLEWARE] registering middleware stack")

    try:
        # register_rate_limit(app)
        register_logging(app)
        logger.info("[MIDDLEWARE] logging middleware registered SUCCESS")

    except Exception:
        logger.exception("[MIDDLEWARE] middleware registration FAILED")
        raise


# ---- Logging Middleware Registration ----
def register_logging(app):

    logger.info("[MIDDLEWARE] initializing HTTP logging middleware")

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()

        # ---- Request Start Logging ----
        log_start(request)

        try:
            response = await call_next(request)
        except Exception as e:
            # ---- Error Logging ----
            log_error(request, start_time, e)
            raise

        # ---- Success Logging ----
        log_success(request, response, start_time)

        return response


# ---- Request Start Logger ----
def log_start(request: Request):
    logger.info("[HTTP] incoming request | %s %s", request.method, request.url)


# ---- Request Success Logger ----
def log_success(request: Request, response, start_time: float):
    process_time = time.time() - start_time

    logger.info(
        "[HTTP] response success | %s %s | status=%s | time=%.4fs",
        request.method,
        request.url,
        response.status_code,
        process_time
    )


# ---- Request Error Logger ----
def log_error(request: Request, start_time: float, error: Exception):
    process_time = time.time() - start_time

    logger.exception(
        "[HTTP] request failed | %s %s | time=%.4fs | error=%s",
        request.method,
        request.url,
        process_time,
        str(error)
    )