# ---- Imports ----
from fastapi import APIRouter, status, Depends
from uuid_utils import uuid4
from source.infra_service.api.models.chunks_db_model import ChunkIn
from source.infra_service.core.di.dependencies import get_chunking_use_case
from source.infra_service.core.errors.exceptions import (
    ValidationException,
    ServiceUnavailableException,
    InternalServerException,
)
import logging

# ---- Logger ----
logger = logging.getLogger(__name__)

router = APIRouter()

# ---- Health Check ----
@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(
    chunking_use_case=Depends(get_chunking_use_case)
):
    try:
        await chunking_use_case.health()
        return {"message": "Chunking service is up"}
    except Exception:
        logger.exception("[Chunking Routes] health check failed")
        raise ServiceUnavailableException("Chunking")


# ---- Initialize Chunks Table ----
@router.get("/init")
async def init_chunking_table(
    chunking_use_case=Depends(get_chunking_use_case),
):
    try:
        already_initialized = await chunking_use_case.init()

        if already_initialized:
            return {
                "message": "Chunks_table already initialized",
                "status": status.HTTP_200_OK,
            }

        return {
            "message": "Chunks_table initialized",
            "status": status.HTTP_201_CREATED,
        }

    except Exception:
        logger.exception("[Chunking Routes] init failed")
        raise InternalServerException("Failed to initialize chunks_table")


# ---- Delete All Chunks ----
@router.delete("/delete_all_chunks", status_code=status.HTTP_200_OK)
async def delete_chunks(
    chunking_use_case=Depends(get_chunking_use_case),
):
    try:
        await chunking_use_case.delete_all()
        return {"message": "All chunks deleted"}

    except Exception:
        logger.exception("[Chunking Routes] delete failed")
        raise InternalServerException("Failed to delete chunks")


# ---- Drop Chunks Table ----
@router.delete("/drop_chunks_table", status_code=status.HTTP_200_OK)
async def drop_chunks_table(
    chunking_use_case=Depends(get_chunking_use_case),
):
    try:
        await chunking_use_case.drop_table()
        return {"message": "Chunks_table dropped"}

    except Exception:
        logger.exception("[Chunking Routes] drop failed")
        raise InternalServerException("Failed to drop chunks_table")


# ---- Count Chunks ----
@router.get("/count_chunks", status_code=status.HTTP_200_OK)
async def count_chunks(
    chunking_use_case=Depends(get_chunking_use_case),
):
    try:
        count = await chunking_use_case.count()
        return {"message": f"Total chunks: {count}", "count": count}

    except Exception:
        logger.exception("[Chunking Routes] count failed")
        raise InternalServerException("Failed to count chunks")


# ---- Insert Chunks ----
@router.post("/insert_chunks", status_code=status.HTTP_200_OK)
async def insert_chunks(
    chunks: list[ChunkIn],
    chunking_use_case=Depends(get_chunking_use_case),
):
    if not chunks:
        raise ValidationException("chunks list is empty")

    try:
        payload = []

        for c in chunks:
            item = c.model_dump()
            item["id"] = str(uuid4())  # server-side ownership
            payload.append(item)

        await chunking_use_case.upsert(payload)

        return {
            "message": f"Inserted {len(payload)} chunks",
            "count": len(payload),
        }

    except Exception:
        logger.exception("[Chunking Routes] insert failed")
        raise InternalServerException("Failed to insert chunks")