import time
import logging
from fastapi import Request

# from rate_limit.middleware import RateLimitMiddleware

logger = logging.getLogger(__name__)


def register_middleware(app):
    # register_rate_limit(app)
    register_logging(app)


# def register_rate_limit(app):
#     app.add_middleware(RateLimitMiddleware)


def register_logging(app):

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()

        log_start(request)

        try:
            response = await call_next(request)
        except Exception as e:
            log_error(request, start_time, e)
            raise

        log_success(request, response, start_time)

        return response


def log_start(request: Request):
    logger.info(f"Incoming request: {request.method} {request.url}")


def log_success(request: Request, response, start_time: float):
    process_time = time.time() - start_time

    logger.info(
        f"Response: {request.method} {request.url} "
        f"Status={response.status_code} "
        f"Time={process_time:.4f}s"
    )


def log_error(request: Request, start_time: float, error: Exception):
    process_time = time.time() - start_time

    logger.exception(
        f"Request failed: {request.method} {request.url} "
        f"Time={process_time:.4f}s Error={str(error)}"
    )