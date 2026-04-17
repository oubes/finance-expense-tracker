from fastapi import APIRouter, Response, status
from source.infra_service.core.di.dependencies import get_llm_service

router = APIRouter()

@router.post("/generate")
async def generate(message: list[dict[str, str]]):
    llm_service = await get_llm_service()
    response = await llm_service.generate(message)
    return Response(
        content=response,
        status_code=status.HTTP_200_OK,
        media_type="application/json"
    )