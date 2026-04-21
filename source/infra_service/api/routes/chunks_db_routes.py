# ---- Imports ----
from fastapi import APIRouter, status, Depends
from uuid_utils import uuid4

from source.infra_service.api.models.chunks_db_model import (
    ChunkIn,
    ChunkBatchIn,
    BM25SearchRequest,
    VectorSearchRequest,
    HybridSearchRequest,
    SearchResponse,
    CountResponse,
    ChunkOut,
    HealthCheckResponse,
    InitTableResponse,
    DeleteChunksResponse,
    DropTableResponse,
    InsertChunksRequest,
    InsertChunksResponse,
)

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
@router.get("/health", response_model=HealthCheckResponse, status_code=status.HTTP_200_OK)
async def health_check(
    chunking_use_case=Depends(get_chunking_use_case)
):
    try:
        await chunking_use_case.health()
        return HealthCheckResponse(message="Chunking service is up")
    except Exception:
        logger.exception("[Chunking Routes] health check failed")
        raise ServiceUnavailableException("Chunking")


# ---- Initialize Chunks Table ----
@router.get("/init", response_model=InitTableResponse)
async def init_chunking_table(
    chunking_use_case=Depends(get_chunking_use_case),
):
    try:
        already_initialized = await chunking_use_case.init()
        
        if already_initialized:
            return InitTableResponse(
                message="Chunks_table already initialized",
                status=status.HTTP_200_OK,
            )
        

        return InitTableResponse(
            message="Chunks_table initialized",
            status=status.HTTP_201_CREATED,
        )

    except Exception:
        logger.exception("[Chunking Routes] init failed")
        raise InternalServerException("Failed to initialize chunks_table")


# ---- Count Chunks ----
@router.get("/count_chunks", response_model=CountResponse, status_code=status.HTTP_200_OK)
async def count_chunks(
    chunking_use_case=Depends(get_chunking_use_case),
):
    try:
        count = await chunking_use_case.count()
        return CountResponse(
            count=count,
            message=f"Total chunks: {count}",
        )
    except Exception:
        logger.exception("[Chunking Routes] count failed")
        raise InternalServerException("Failed to count chunks")


# ---- Insert Chunks ----
@router.post("/insert_chunks", response_model=InsertChunksResponse, status_code=status.HTTP_200_OK)
async def insert_chunks(
    body: InsertChunksRequest,
    chunking_use_case=Depends(get_chunking_use_case),
):
    if not body.chunks:
        raise ValidationException("chunks list is empty")

    try:
        payload = []
        for c in body.chunks:
            item = c.model_dump()
            item["id"] = str(uuid4())
            payload.append(item)

        await chunking_use_case.upsert(payload)

        return InsertChunksResponse(
            message=f"Inserted {len(payload)} chunks",
            count=len(payload),
        )

    except Exception:
        logger.exception("[Chunking Routes] insert failed")
        raise InternalServerException("Failed to insert chunks")


# ---- BM25 Search ----
@router.post("/search/bm25", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def bm25_search(
    body: BM25SearchRequest,
    chunking_use_case=Depends(get_chunking_use_case),
):
    if not body.query:
        raise ValidationException("query is required")

    try:
        results = await chunking_use_case.bm25_search(body.query, body.limit)

        normalized = [ChunkOut.model_validate(r) for r in results]

        return SearchResponse(
            query=body.query,
            count=len(normalized),
            results=normalized,
        )

    except Exception:
        logger.exception("[Chunking Routes] bm25 search failed")
        raise InternalServerException("BM25 search failed")


# ---- Vector Search ----
@router.post("/search/vector", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def vector_search(
    body: VectorSearchRequest,
    chunking_use_case=Depends(get_chunking_use_case),
):
    if not body.embedding:
        raise ValidationException("embedding is required")

    try:
        results = await chunking_use_case.vector_search(body.embedding, body.limit)

        normalized = [ChunkOut.model_validate(r) for r in results]

        return SearchResponse(
            count=len(normalized),
            results=normalized,
        )

    except Exception:
        logger.exception("[Chunking Routes] vector search failed")
        raise InternalServerException("Vector search failed")


# ---- Hybrid Search ----
@router.post("/search/hybrid", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def hybrid_search(
    body: HybridSearchRequest,
    chunking_use_case=Depends(get_chunking_use_case),
):
    if not body.query:
        raise ValidationException("query is required")

    if body.embedding is None:
        raise ValidationException("embedding is required")

    try:
        results = await chunking_use_case.hybrid_search(
            query=body.query,
            embedding=body.embedding,
            limit=body.limit,
            weights=body.weights,
        )

        normalized = [ChunkOut.model_validate(r) for r in results]

        return SearchResponse(
            query=body.query,
            count=len(normalized),
            results=normalized,
        )

    except Exception:
        logger.exception("[Chunking Routes] hybrid search failed")
        raise InternalServerException("Hybrid search failed")
    
# ---- Delete All Chunks ----
@router.delete("/delete_all_chunks", response_model=DeleteChunksResponse, status_code=status.HTTP_200_OK)
async def delete_chunks(
    chunking_use_case=Depends(get_chunking_use_case),
):
    try:
        await chunking_use_case.delete_all()
        return DeleteChunksResponse(message="All chunks deleted")

    except Exception:
        logger.exception("[Chunking Routes] delete failed")
        raise InternalServerException("Failed to delete chunks")


# ---- Drop Chunks Table ----
@router.delete("/drop_chunks_table", response_model=DropTableResponse, status_code=status.HTTP_200_OK)
async def drop_chunks_table(
    chunking_use_case=Depends(get_chunking_use_case),
):
    try:
        result = await chunking_use_case.drop_table()

        if result:
            return DropTableResponse(message="chunks_table dropped successfully")

        return DropTableResponse(message="chunks_table does not exist")

    except Exception:
        logger.exception("[Chunking Routes] drop failed")
        raise InternalServerException("Failed to drop chunks_table")