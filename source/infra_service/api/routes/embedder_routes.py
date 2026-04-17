from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from source.infra_service.core.di.dependencies import get_embedding_service

router = APIRouter()

@router.post("/embed")
async def embed(
    message: str,
    embedding_service = Depends(get_embedding_service)
):
    embedding = await embedding_service.embed(message)
    return JSONResponse(
        content=embedding,
        status_code=status.HTTP_200_OK,
        media_type="application/json"
    )