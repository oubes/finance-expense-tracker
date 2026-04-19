from fastapi import APIRouter, Depends, status

from source.infra_service.application.services.llm_service import LLMService
from source.infra_service.api.models.llm_model import (
    ChatRequest,
    ChatResponse,
    BatchChatRequest,
    BatchChatResponse,
    BatchChatItemResponse,
)
from source.infra_service.core.di.dependencies import get_llm_service, get_settings
from source.infra_service.core.errors.exceptions import (
    ServiceUnavailableException,
    InternalServerException,
    ValidationException,
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ---- ACTIVE HEALTH CHECK ----
@router.get("/health", status_code=status.HTTP_200_OK)
async def health(
    llm_service: LLMService = Depends(get_llm_service),
):
    try:
        messages = [{"role": "user", "content": "Hi"}]

        response = await llm_service.generate(
            messages=messages,
            temperature=0.0,
            max_tokens=5,
        )

        if not response:
            raise ServiceUnavailableException("LLM")

        return {
            "status": "up",
            "service": "llm",
            "response_sample": response,
        }

    except ServiceUnavailableException:
        logger.exception("[LLM Routes] unhealthy LLM service")
        raise

    except Exception:
        logger.exception("[LLM Routes] health check failed")
        raise ServiceUnavailableException("LLM")


# ---- SINGLE ----
@router.post("/generate", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def generate(
    message: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
    settings=Depends(get_settings),
):
    if not message.user_message:
        raise ValidationException("user_message is empty")

    try:
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

    except Exception:
        logger.exception("[LLM Routes] generate failed")
        raise InternalServerException("Failed to generate response")


# ---- BATCH ----
@router.post("/generate_batch", response_model=BatchChatResponse, status_code=status.HTTP_200_OK)
async def generate_batch(
    payload: BatchChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
    settings=Depends(get_settings),
):
    if not payload.messages:
        raise ValidationException("messages list is empty")

    try:
        results = []

        for msg in payload.messages:
            if not msg.user_message:
                raise ValidationException("one of the messages has empty user_message")

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

    except ValidationException:
        raise

    except Exception:
        logger.exception("[LLM Routes] batch generate failed")
        raise InternalServerException("Failed to generate batch responses")