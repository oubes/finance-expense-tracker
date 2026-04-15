from fastapi import APIRouter, Depends, Response, status
import logging

from source.api_gateway.core.di.dependencies import get_ingestion_service
from source.api_gateway.application.ingestion_service import IngestionService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/ingestion/health")
async def ingestion_health(
    service: IngestionService = Depends(get_ingestion_service),
):
    logger.info("ingestion health check started")

    result = await service.health()

    if result.status == "up":
        return result

    if result.status == "degraded":
        return Response(
            content=result.model_dump_json(),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json",
        )

    return Response(
        content=result.model_dump_json(),
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        media_type="application/json",
    )