import time
import logging
from fastapi import Request

from source.api_gateway.core.observability.context import (
    set_request_context,
    get_request_id,
    get_trace_id,
    generate_id,
    reset_context,
)

logger = logging.getLogger(__name__)


def register_middleware(app):
    logger.info("[MIDDLEWARE] registering middleware stack")
    register_logging(app)


def register_logging(app):

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        return await _handle_request(request, call_next)


async def _handle_request(request: Request, call_next):
    start_time = time.time()

    request_id = request.headers.get("x-request-id") or generate_id()
    trace_id = request.headers.get("x-trace-id") or generate_id()

    set_request_context(
        request_id=request_id,
        trace_id=trace_id,
        service_name="api_gateway",
    )

    request.state.request_id = request_id
    request.state.trace_id = trace_id

    logger.info(
        "[HTTP] incoming request | %s %s | req=%s | trace=%s",
        request.method,
        request.url,
        get_request_id(),
        get_trace_id(),
    )

    try:
        response = await call_next(request)
        return response

    except Exception as e:
        logger.exception(
            "[HTTP] request failed | %s %s | error=%s | req=%s | trace=%s",
            request.method,
            request.url,
            str(e),
            get_request_id(),
            get_trace_id(),
        )
        raise

    finally:
        reset_context()