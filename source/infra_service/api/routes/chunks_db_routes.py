# ---- Imports ----
from fastapi import APIRouter, status, Depends
from uuid_utils import uuid4

from source.infra_service.api.models.chunks_db_model import (
    BM25SearchRequest,
    VectorSearchRequest,
    HybridSearchRequest,
    SearchResponse,
    CountResponse,
    HealthCheckResponse,
    InitTableResponse,
    DeleteChunksResponse,
    DropTableResponse,
    InsertChunksRequest,
    InsertChunksResponse,
    GetChunkByIdResponse,
    GetChunksByPagesRequest,
    GetChunksByPagesResponse,
    UpdateChunkRequest,
    UpdateChunkResponse,
    DeleteChunkResponse,
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


# -------------------- GET OPERATIONS --------------------

# ---- HEALTH ----
@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK
)
async def health_check(chunking_use_case=Depends(get_chunking_use_case)):
    try:
        await chunking_use_case.health()
        return HealthCheckResponse(message="Chunking service is up")
    except Exception:
        logger.exception("[Chunking Routes] health check failed")
        raise ServiceUnavailableException("Chunking")


# ---- INIT ----
@router.get(
    "/init",
    response_model=InitTableResponse,
    status_code=status.HTTP_200_OK
)
async def init(chunking_use_case=Depends(get_chunking_use_case)):
    try:
        already = await chunking_use_case.init()

        if already:
            return InitTableResponse(
                message="already initialized",
                status=status.HTTP_200_OK,
            )

        return InitTableResponse(
            message="initialized",
            status=status.HTTP_201_CREATED,
        )

    except Exception:
        logger.exception("[Chunking Routes] init failed")
        raise InternalServerException("init failed")


# ---- COUNT ----
@router.get(
    "/count",
    response_model=CountResponse,
    status_code=status.HTTP_200_OK
)
async def count(chunking_use_case=Depends(get_chunking_use_case)):
    try:
        count = await chunking_use_case.count()
        return CountResponse(count=count, message=f"Total chunks: {count}")
    except Exception:
        logger.exception("[Chunking Routes] count failed")
        raise InternalServerException("count failed")


# ---- GET BY ID ----
@router.get(
    "/chunks/{chunk_id}",
    response_model=GetChunkByIdResponse,
    status_code=status.HTTP_200_OK
)
async def get_chunk(chunk_id: str, chunking_use_case=Depends(get_chunking_use_case)):
    try:
        result = await chunking_use_case.get_chunk_by_id(chunk_id)
        return GetChunkByIdResponse(result=result)
    except Exception:
        logger.exception("[Chunking Routes] get by id failed")
        raise InternalServerException("get failed")


# -------------------- POST OPERATIONS --------------------

# ---- INSERT ----
@router.post(
    "/insert_chunks",
    response_model=InsertChunksResponse,
    status_code=status.HTTP_201_CREATED
)
async def insert(body: InsertChunksRequest, chunking_use_case=Depends(get_chunking_use_case)):
    if not body.chunks:
        raise ValidationException("empty chunks")

    try:
        payload = []
        for c in body.chunks:
            item = c.model_dump()
            item["id"] = str(uuid4())
            payload.append(item)

        await chunking_use_case.upsert(payload)

        return InsertChunksResponse(
            message="inserted",
            count=len(payload),
        )

    except Exception:
        logger.exception("[Chunking Routes] insert failed")
        raise InternalServerException("insert failed")


# ---- BM25 SEARCH ----
@router.post(
    "/search/bm25",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK
)
async def bm25(body: BM25SearchRequest, chunking_use_case=Depends(get_chunking_use_case)):
    try:
        res = await chunking_use_case.bm25_search(body.query, body.limit)
        return SearchResponse(query=body.query, count=len(res), results=res)
    except Exception:
        logger.exception("[Chunking Routes] bm25 failed")
        raise InternalServerException("bm25 failed")


# ---- VECTOR SEARCH ----
@router.post(
    "/search/vector",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK
)
async def vector(body: VectorSearchRequest, chunking_use_case=Depends(get_chunking_use_case)):
    try:
        res = await chunking_use_case.vector_search(body.embedding, body.limit)
        return SearchResponse(count=len(res), results=res)
    except Exception:
        logger.exception("[Chunking Routes] vector failed")
        raise InternalServerException("vector failed")


# ---- HYBRID SEARCH ----
@router.post(
    "/search/hybrid",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK
)
async def hybrid(body: HybridSearchRequest, chunking_use_case=Depends(get_chunking_use_case)):
    try:
        res = await chunking_use_case.hybrid_search(
            body.query,
            body.embedding,
            body.limit,
            body.weights,
        )
        return SearchResponse(query=body.query, count=len(res), results=res)
    except Exception:
        logger.exception("[Chunking Routes] hybrid failed")
        raise InternalServerException("hybrid failed")


# ---- GET BY PAGES ----
@router.post(
    "/chunks/by_pages",
    response_model=GetChunksByPagesResponse,
    status_code=status.HTTP_200_OK
)
async def get_by_pages(body: GetChunksByPagesRequest, chunking_use_case=Depends(get_chunking_use_case)):
    try:
        res = await chunking_use_case.get_chunks_by_pages(body.pages)
        return GetChunksByPagesResponse(count=len(res), results=res)
    except Exception:
        logger.exception("[Chunking Routes] get pages failed")
        raise InternalServerException("pages failed")


# -------------------- PATCH OPERATIONS --------------------

# ---- UPDATE ----
@router.patch(
    "/chunks/{chunk_id}",
    response_model=UpdateChunkResponse,
    status_code=status.HTTP_200_OK
)
async def update_chunk(chunk_id: str, body: UpdateChunkRequest, chunking_use_case=Depends(get_chunking_use_case)):
    try:
        data = body.data.model_dump()
        data["id"] = chunk_id

        await chunking_use_case.update_chunk(tuple(data.values()))
        return UpdateChunkResponse(message="updated")

    except Exception:
        logger.exception("[Chunking Routes] update failed")
        raise InternalServerException("update failed")


# -------------------- DELETE OPERATIONS --------------------

# ---- DELETE BY ID ----
@router.delete(
    "/chunks/{chunk_id}",
    response_model=DeleteChunkResponse,
    status_code=status.HTTP_200_OK
)
async def delete_chunk(chunk_id: str, chunking_use_case=Depends(get_chunking_use_case)):
    try:
        ok = await chunking_use_case.delete_chunk_by_id(chunk_id)
        return DeleteChunkResponse(success=ok)
    except Exception:
        logger.exception("[Chunking Routes] delete failed")
        raise InternalServerException("delete failed")


# ---- DELETE ALL ----
@router.delete(
    "/delete_all_chunks",
    response_model=DeleteChunksResponse,
    status_code=status.HTTP_200_OK
)
async def delete_all(chunking_use_case=Depends(get_chunking_use_case)):
    try:
        await chunking_use_case.delete_all()
        return DeleteChunksResponse(message="deleted all")
    except Exception:
        logger.exception("[Chunking Routes] delete all failed")
        raise InternalServerException("delete all failed")


# ---- DROP ----
@router.delete(
    "/drop_chunks_table",
    response_model=DropTableResponse,
    status_code=status.HTTP_200_OK
)
async def drop(chunking_use_case=Depends(get_chunking_use_case)):
    try:
        ok = await chunking_use_case.drop_table()

        if ok:
            return DropTableResponse(message="dropped")

        return DropTableResponse(message="not exists")

    except Exception:
        logger.exception("[Chunking Routes] drop failed")
        raise InternalServerException("drop failed")