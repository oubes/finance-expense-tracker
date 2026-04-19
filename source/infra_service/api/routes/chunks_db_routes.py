# ---- Imports ----
from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from uuid_utils import uuid4
from source.infra_service.api.models.chunks_db_model import ChunkIn
from source.infra_service.core.di.dependencies import (
    get_chunking_use_case,
)
import logging

# ---- Logger ----
logger = logging.getLogger(__name__)

router = APIRouter()

# ---- Routes ----
# ---- Health Check ----
@router.get("/health")
async def health_check(
    chunking_use_case=Depends(get_chunking_use_case)
) -> JSONResponse:
    try:
        await chunking_use_case.health()
        status_code = status.HTTP_200_OK
        return JSONResponse(
            content={
                "message": "Chunking service is up",
            },
            status_code=status_code,
        )
    except Exception as e:
        logger.exception("[Chunking Routes] health check failed")
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return JSONResponse(
            content={
                "message": "Chunking service is unavailable",
            },
            status_code=status_code,
        )

# --- Initialize Chunks Table ----
@router.get("/init")
async def init_chunking_table(
    chunking_use_case=Depends(get_chunking_use_case),
) -> JSONResponse:
    try:
        already_initialized = await chunking_use_case.init()
        if already_initialized:
            status_code = status.HTTP_200_OK
            return JSONResponse(
                content={
                    "message": "Chunks_table already initialized",
                },
                status_code=status_code,
            )
        else:
            status_code = status.HTTP_201_CREATED
            return JSONResponse(
                content={
                    "message": "Chunks_table initialized",
                },
                status_code=status_code,
            )
    except Exception as e:
        logger.exception("[Chunking Routes] init failed")
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return JSONResponse(
            content={
                "message": "Failed to initialize chunks_table",
            },
            status_code=status_code,
        )
        
# --- Delete All Chunks ----
@router.delete("/delete_all_chunks")
async def delete_chunks(
    chunking_use_case=Depends(get_chunking_use_case),
) -> JSONResponse:
    try:
        await chunking_use_case.delete_all()
        status_code = status.HTTP_200_OK
        return JSONResponse(
            content={
                "message": "All chunks deleted",
            },
            status_code=status_code,
        )
    except Exception as e:
        logger.exception("[Chunking Routes] delete failed")
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return JSONResponse(
            content={
                "message": "Failed to delete chunks",
            },
            status_code=status_code,
        )

# --- Drop Chunks Table ----
@router.delete("/drop_chunks_table")
async def drop_chunks_table(
    chunking_use_case=Depends(get_chunking_use_case),
) -> JSONResponse:
    try:
        await chunking_use_case.drop_table()
        status_code = status.HTTP_200_OK
        return JSONResponse(
            content={
                "message": "Chunks_table dropped",
            },
            status_code=status_code,
        )
    except Exception as e:
        logger.exception("[Chunking Routes] drop failed")
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return JSONResponse(
            content={
                "message": "Failed to drop chunks_table",
            },
            status_code=status_code,
        )
        
# ---- Count Chunks ----
@router.get("/count_chunks")
async def count_chunks(
    chunking_use_case=Depends(get_chunking_use_case),
) -> JSONResponse:
    try:
        count = await chunking_use_case.count()
        status_code = status.HTTP_200_OK
        return JSONResponse(
            content={
                "message": f"Total chunks: {count}",
            },
            status_code=status_code,
        )
    except Exception as e:
        logger.exception("[Chunking Routes] count failed")
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return JSONResponse(
            content={
                "message": "Failed to count chunks"
            },
            status_code=status_code,
        )
        
# ---- Insert Chunks ----
@router.post("/insert_chunks")
async def insert_chunks(
    chunks: list[ChunkIn],
    chunking_use_case=Depends(get_chunking_use_case),
) -> JSONResponse:

    if not chunks:
        status_code = status.HTTP_400_BAD_REQUEST
        return JSONResponse(
            content={
                "message": "chunks list is empty",
            },
            status_code=status_code,
        )

    try:
        payload = []

        for c in chunks:
            item = c.model_dump()
            item["id"] = str(uuid4())  # server-side ownership
            payload.append(item)

        await chunking_use_case.upsert(payload)

        status_code=status.HTTP_200_OK
        return JSONResponse(
            content={
                "message": f"Inserted {len(payload)} chunks",
                "count": len(payload),
            },
            status_code=status_code,
        )
    except Exception:
        logger.exception("[Chunking Routes] insert failed")
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return JSONResponse(
            content={
                "message": "Failed to insert chunks",
            },
            status_code=status_code,
        )
    
