from fastapi import APIRouter, Depends
from source.api_gateway.core.di.dependencies import get_ingestion_service
from source.api_gateway.application.ingestion_service import IngestionService

router = APIRouter()

@router.get("/ingestion/health")
async def ingestion_health(service: IngestionService = Depends(get_ingestion_service)):
    return await service.health()