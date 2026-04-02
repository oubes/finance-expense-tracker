import asyncio
from fastapi import Response, status

from src.core.config.loader import load_settings
from .app_health import get_app_health
from .db_health import check_db
from .redis_health import check_redis


async def get_readiness(response: Response):
    settings = load_settings()

    dependencies = {}

    # App Health
    try:
        app = get_app_health()
        dependencies["app"] = {
            "status": "success",
            "data": app.model_dump(),
        }
        app_ok = True
    except Exception as e:
        dependencies["app"] = {
            "status": "failed",
            "error": str(e),
        }
        app_ok = False

    # DB Health
    try:
        db_status = await check_db(settings)
        dependencies["database"] = {
            "status": "success" if db_status.healthy else "failed",
            "data": db_status.model_dump(),
        }
        db_ok = db_status.healthy
    except Exception as e:
        dependencies["database"] = {
            "status": "failed",
            "error": str(e),
        }
        db_ok = False

    # Redis Health
    try:
        redis_status = await check_redis(settings)
        dependencies["redis"] = {
            "status": "success" if redis_status.healthy else "failed",
            "data": redis_status.model_dump(),
        }
        redis_ok = redis_status.healthy
    except Exception as e:
        dependencies["redis"] = {
            "status": "failed",
            "error": str(e),
        }
        redis_ok = False

    # Overall status
    all_ok = app_ok and db_ok and redis_ok

    response.status_code = (
        status.HTTP_200_OK
        if all_ok
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return {
        "status": "ready" if all_ok else "not_ready",
        "dependencies": dependencies,
    }