from fastapi import APIRouter, Depends, status

from source.infra_service.core.di.dependencies import get_embedding_service
from source.infra_service.api.models.embedder_model import (
    EmbedRequest,
    EmbedResponse,
    BatchEmbedRequest,
    BatchEmbedResponse,
    BatchEmbedItem,
)
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
    embedding_service=Depends(get_embedding_service),
):
    try:
        test_text = "Hi"

        embedding = await embedding_service.embed(test_text)

        if not embedding or len(embedding) == 0:
            raise ServiceUnavailableException("Embedding")

        return {
            "status": "up",
            "service": "embedding",
            "embedding_dim": len(embedding),
        }

    except ServiceUnavailableException:
        logger.exception("[Embedding Routes] unhealthy embedding service")
        raise

    except Exception:
        logger.exception("[Embedding Routes] health check failed")
        raise ServiceUnavailableException("Embedding")


# ---- SINGLE EMBED ----
@router.post("/embed", response_model=EmbedResponse, status_code=status.HTTP_200_OK)
async def embed(
    payload: EmbedRequest,
    embedding_service=Depends(get_embedding_service),
):
    if not payload.text:
        raise ValidationException("text is empty")

    try:
        embedding = await embedding_service.embed(payload.text)
        return EmbedResponse(embedding=embedding)

    except Exception:
        logger.exception("[Embedding Routes] embed failed")
        raise InternalServerException("Failed to generate embedding")


# ---- BATCH EMBED ----
@router.post("/embed_batch", response_model=BatchEmbedResponse, status_code=status.HTTP_200_OK)
async def embed_batch(
    payload: BatchEmbedRequest,
    embedding_service=Depends(get_embedding_service),
):
    if not payload.texts:
        raise ValidationException("texts list is empty")

    try:
        results = []

        for text in payload.texts:
            if not text:
                raise ValidationException("one of the texts is empty")

            embedding = await embedding_service.embed(text)

            results.append(
                BatchEmbedItem(
                    text=text,
                    embedding=embedding,
                )
            )

        return BatchEmbedResponse(
            results=results,
            count=len(results),
        )

    except ValidationException:
        raise

    except Exception:
        logger.exception("[Embedding Routes] batch embed failed")
        raise InternalServerException("Failed to generate batch embeddings")