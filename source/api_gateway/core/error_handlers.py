# ---------- core/error_handlers.py ----------

import logging
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

from source.api_gateway.core.exceptions import BaseAPIException

logger = logging.getLogger(__name__)


# ---------- Base API Exception Handler ----------

async def base_exception_handler(request: Request, exc: Exception):
    request_id = str(uuid.uuid4())

    if isinstance(exc, BaseAPIException):
        logger.warning(
            f"[{request_id}] {exc.error_code} | {exc.message}",
            extra={
                "request_id": request_id,
                "error_code": exc.error_code,
                "path": request.url.path,
                "details": exc.details,
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "request_id": request_id,
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )

    logger.exception(
        f"[{request_id}] unexpected error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "request_id": request_id,
            "error": {
                "code": "internal_error",
                "message": "Unexpected server error",
            },
        },
    )


# ---------- Generic Exception Handler ----------

async def generic_exception_handler(request: Request, exc: Exception):
    request_id = str(uuid.uuid4())

    logger.exception(
        f"[{request_id}] unhandled error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "request_id": request_id,
            "error": {
                "code": "internal_error",
                "message": "Unexpected server error",
            },
        },
    )