from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from source.infra_service.application.services.llm_service import LLMService
from source.infra_service.api.models.llm_model import ChatMessage
from source.infra_service.core.di.dependencies import get_llm_service

router = APIRouter()

@router.post("/generate")
async def generate(
    message: ChatMessage,
    llm_service: LLMService = Depends(get_llm_service)
):

    messages = [
        {"role": "system", "content": message.ai_message},
        {"role": "user", "content": message.user_message},
    ]
    response = await llm_service.generate(
        messages,
        message.temperature,
    )

    return JSONResponse(
        content=response,
        status_code=status.HTTP_200_OK,
    )