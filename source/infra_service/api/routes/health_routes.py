from fastapi import APIRouter, status
from source.infra_service.core.errors.exceptions import ServiceUnavailableException

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    try:
        return {
            "status": "up",
        }

    except Exception:
        raise ServiceUnavailableException("Core")