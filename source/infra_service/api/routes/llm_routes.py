from fastapi import APIRouter, Depends
from source.infra_service.application.services.llm_service import LLMService
from source.infra_service.api.models.llm_model import (
    ChatRequest,
    ChatResponse,
    BatchChatRequest,
    BatchChatResponse,
    BatchChatItemResponse,
)
from source.infra_service.core.di.dependencies import get_llm_service, get_settings

router = APIRouter()


# ---- SINGLE ----
@router.post("/generate", response_model=ChatResponse)
async def generate(
    message: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
    settings=Depends(get_settings),
):

    messages = [
        {"role": "system", "content": message.ai_message},
        {"role": "user", "content": message.user_message},
    ]

    response = await llm_service.generate(
        messages,
        message.temperature,
        settings.llm.max_tokens,
    )

    return ChatResponse(response=response)


# ---- BATCH ----
@router.post("/generate_batch", response_model=BatchChatResponse)
async def generate_batch(
    payload: BatchChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
    settings=Depends(get_settings),
):

    results = []

    for msg in payload.messages:

        formatted_messages = [
            {"role": "system", "content": msg.ai_message},
            {"role": "user", "content": msg.user_message},
        ]

        response = await llm_service.generate(
            messages=formatted_messages,
            temperature=msg.temperature,
            max_tokens=settings.llm.max_tokens,
        )

        results.append(
            BatchChatItemResponse(response=response)
        )

    return BatchChatResponse(
        results=results,
        count=len(results),
    )