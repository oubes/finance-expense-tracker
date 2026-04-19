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