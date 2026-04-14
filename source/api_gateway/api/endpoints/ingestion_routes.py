from fastapi import APIRouter, Depends
from source.api_gateway.clients.ingestion import IngestionClient
from source.api_gateway.core.dependencies import get_ingestion_client

router = APIRouter()

@router.get("/ingestion/health")
async def ingestion_health(client: IngestionClient = Depends(get_ingestion_client)):
    return await client.health()