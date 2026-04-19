from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from source.infra_service.core.di.dependencies import get_embedding_service
from source.infra_service.api.models.embedder_model import (
    EmbedRequest,
    EmbedResponse,
    BatchEmbedRequest,
    BatchEmbedResponse,
    BatchEmbedItem,
)

router = APIRouter()


# ---- ACTIVE HEALTH CHECK ----
@router.get("/health")
async def health(
    embedding_service=Depends(get_embedding_service),
):
    try:
        test_text = "Hi"

        embedding = await embedding_service.embed(test_text)

        if not embedding or len(embedding) == 0:
            raise ValueError("Empty embedding response")

        return JSONResponse(
            content={
                "status": "up",
                "service": "embedding",
                "embedding_dim": len(embedding),
            },
            status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        return JSONResponse(
            content={
                "status": "down",
                "error": str(e),
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# ---- SINGLE EMBED ----
@router.post("/embed", response_model=EmbedResponse)
async def embed(
    payload: EmbedRequest,
    embedding_service=Depends(get_embedding_service),
):

    embedding = await embedding_service.embed(payload.text)

    return EmbedResponse(embedding=embedding)


# ---- BATCH EMBED ----
@router.post("/embed_batch", response_model=BatchEmbedResponse)
async def embed_batch(
    payload: BatchEmbedRequest,
    embedding_service=Depends(get_embedding_service),
):

    results = []

    for text in payload.texts:

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