# ---- Imports ----
from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from source.infra_service.core.di.dependencies import (
    get_chunking_use_case,
)
import logging

# ---- Logger ----
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check(
    chunking_use_case=Depends(get_chunking_use_case)
) -> JSONResponse:
    try:
        await chunking_use_case.health()
        status_code = status.HTTP_200_OK
        return JSONResponse(
            content={"message": "Chunking service is healthy", "status_code": status_code},
            status_code=status_code,
        )
    except Exception as e:
        logger.exception("[Chunking Routes] health check failed")
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return JSONResponse(
            content={"message": "Chunking service is unavailable", "status_code": status_code},
            status_code=status_code,
        )

@router.get("/init")
async def init_chunking_table(
    chunking_use_case=Depends(get_chunking_use_case),
) -> JSONResponse:
    try:
        already_initialized = await chunking_use_case.init()
        if already_initialized:
            status_code = status.HTTP_200_OK
            return JSONResponse(
                content={"message": "Chunks_table already initialized", "status_code": status_code},
                status_code=status_code,
            )
        else:
            status_code = status.HTTP_201_CREATED
            return JSONResponse(
                content={"message": "Chunks_table initialized", "status_code": status_code},
                status_code=status_code,
            )
    except Exception as e:
        logger.exception("[Chunking Routes] init failed")
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return JSONResponse(
            content={"message": "Failed to initialize chunks_table", "status_code": status_code},
            status_code=status_code,
        )
        
@router.delete("/delete_all_chunks")
async def delete_chunks(
    chunking_use_case=Depends(get_chunking_use_case),
) -> JSONResponse:
    try:
        await chunking_use_case.delete_all()
        status_code = status.HTTP_200_OK
        return JSONResponse(
            content={"message": "All chunks deleted", "status_code": status_code},
            status_code=status_code,
        )
    except Exception as e:
        logger.exception("[Chunking Routes] delete failed")
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return JSONResponse(
            content={"message": "Failed to delete chunks", "status_code": status_code},
            status_code=status_code,
        )

@router.delete("/drop_chunks_table")
async def drop_chunks_table(
    chunking_use_case=Depends(get_chunking_use_case),
) -> JSONResponse:
    try:
        await chunking_use_case.drop_table()
        status_code = status.HTTP_200_OK
        return JSONResponse(
            content={"message": "Chunks_table dropped", "status_code": status_code},
            status_code=status_code,
        )
    except Exception as e:
        logger.exception("[Chunking Routes] drop failed")
        return JSONResponse(
            content={"message": "Failed to drop chunks_table", "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
