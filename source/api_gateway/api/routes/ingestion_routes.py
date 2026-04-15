from fastapi import APIRouter, Depends
import logging

from source.api_gateway.core.di.dependencies import get_ingestion_service
from source.api_gateway.application.ingestion_service import IngestionService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/ingestion/health")
async def ingestion_health(service: IngestionService = Depends(get_ingestion_service)):
    logger.info("ingestion health check started")
    return await service.health()