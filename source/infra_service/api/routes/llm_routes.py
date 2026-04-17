from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from source.infra_service.application.services.llm_service import LLMService
from source.infra_service.core.di.dependencies import get_llm_service

router = APIRouter()

@router.post("/generate")
async def generate(
    message: list[dict[str, str]],
    llm_service: LLMService = Depends(get_llm_service)
):
    response = await llm_service.generate(message)
    return JSONResponse(
        content=response,
        status_code=status.HTTP_200_OK,
        media_type="application/json"
    )