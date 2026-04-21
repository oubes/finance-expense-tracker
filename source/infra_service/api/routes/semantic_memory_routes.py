# ---- Imports ----
import logging
from fastapi import APIRouter, status, Depends

from source.infra_service.core.di.dependencies import get_semantic_memory_use_case
from source.infra_service.api.models.semantic_memory_model import (
    AddMessageRequest,
    HistoryRequest,
    STMRequest,
    BM25SearchRequest,
    VectorSearchRequest,
    HybridSearchRequest,
    SearchResponse,
    MemoryResponse,
)

from source.infra_service.core.errors.exceptions import (
    ValidationException,
    ServiceUnavailableException,
    InternalServerException,
)

# ---- Logger ----
logger = logging.getLogger(__name__)

router = APIRouter()


# ---- HEALTH CHECK ----
@router.get("/health", status_code=status.HTTP_200_OK)
async def health(
    use_case=Depends(get_semantic_memory_use_case),
):
    try:
        await use_case.health()
        return {"message": "Semantic memory service is up"}

    except Exception:
        logger.exception("[Semantic Memory Routes] health failed")
        raise ServiceUnavailableException("SemanticMemory")


# ---- INIT MEMORY ----
@router.get("/init", response_model=MemoryResponse)
async def init_memory(
    use_case=Depends(get_semantic_memory_use_case),
):
    try:
        already_initialized = await use_case.init()
        print(f"\n\n=====> already_initialized: {already_initialized} <=====\n\n")
        if already_initialized:
            return MemoryResponse(message="semantic_memory already initialized")

        return MemoryResponse(message="semantic_memory initialized")

    except Exception:
        logger.exception("[Semantic Memory Routes] init failed")
        raise InternalServerException("Failed to initialize semantic_memory")


# ---- COUNT ----
@router.get("/count", status_code=status.HTTP_200_OK)
async def count(
    use_case=Depends(get_semantic_memory_use_case),
):
    try:
        value = await use_case.count()
        return {
            "count": value,
            "message": f"Total memory records: {value}",
        }

    except Exception:
        logger.exception("[Semantic Memory Routes] count failed")
        raise InternalServerException("Count failed")


# ---- ADD MESSAGE ----
@router.post("/add", response_model=MemoryResponse, status_code=status.HTTP_200_OK)
async def add_message(
    body: AddMessageRequest,
    use_case=Depends(get_semantic_memory_use_case),
):
    if not body.user_id or not body.session_id or not body.content:
        raise ValidationException("Invalid input")

    try:
        success = await use_case.add_message(
            body.user_id,
            body.session_id,
            body.role,
            body.content,
            body.embedding,
        )

        if not success:
            raise InternalServerException("Insert failed")

        return MemoryResponse(message="message added successfully")

    except Exception:
        logger.exception("[Semantic Memory Routes] add failed")
        raise InternalServerException("Add message failed")


# ---- HISTORY ----
@router.post("/history", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def history(
    body: HistoryRequest,
    use_case=Depends(get_semantic_memory_use_case),
):
    if not body.user_id or not body.session_id:
        raise ValidationException("user_id/session_id required")

    try:
        results = await use_case.get_user_history(
            body.user_id,
            body.session_id,
        )

        return SearchResponse(
            count=len(results),
            results=results,
        )

    except Exception:
        logger.exception("[Semantic Memory Routes] history failed")
        raise InternalServerException("History failed")


# ---- STM ----
@router.post("/stm", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def stm(
    body: STMRequest,
    use_case=Depends(get_semantic_memory_use_case),
):
    if not body.user_id or not body.session_id or body.limit <= 0:
        raise ValidationException("Invalid STM request")

    try:
        results = await use_case.get_stm(
            body.user_id,
            body.session_id,
            body.limit,
        )

        return SearchResponse(
            count=len(results),
            results=results,
        )

    except Exception:
        logger.exception("[Semantic Memory Routes] stm failed")
        raise InternalServerException("STM failed")


# ---- BM25 SEARCH ----
@router.post("/search/bm25", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def bm25_search(
    body: BM25SearchRequest,
    use_case=Depends(get_semantic_memory_use_case),
):
    if not body.user_id or not body.session_id or not body.query:
        raise ValidationException("Invalid BM25 request")

    try:
        results = await use_case.bm25_search(
            body.user_id,
            body.session_id,
            body.query,
            body.limit,
        )

        return SearchResponse(
            count=len(results),
            results=results,
        )

    except Exception:
        logger.exception("[Semantic Memory Routes] bm25 failed")
        raise InternalServerException("BM25 failed")


# ---- VECTOR SEARCH ----
@router.post("/search/vector", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def vector_search(
    body: VectorSearchRequest,
    use_case=Depends(get_semantic_memory_use_case),
):
    if not body.user_id or not body.session_id or body.embedding is None:
        raise ValidationException("Invalid vector request")

    try:
        results = await use_case.vector_search(
            body.user_id,
            body.session_id,
            body.embedding,
            body.limit,
        )

        return SearchResponse(
            count=len(results),
            results=results,
        )

    except Exception:
        logger.exception("[Semantic Memory Routes] vector failed")
        raise InternalServerException("Vector failed")


# ---- HYBRID SEARCH ----
@router.post("/search/hybrid", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def hybrid_search(
    body: HybridSearchRequest,
    use_case=Depends(get_semantic_memory_use_case),
):
    if not body.user_id or not body.session_id or not body.query or body.embedding is None:
        raise ValidationException("Invalid hybrid request")

    try:
        results = await use_case.hybrid_search(
            body.user_id,
            body.session_id,
            body.query,
            body.embedding,
            body.limit,
            body.weights,
        )

        return SearchResponse(
            count=len(results),
            results=results,
        )

    except Exception:
        logger.exception("[Semantic Memory Routes] hybrid failed")
        raise InternalServerException("Hybrid failed")


# ---- DELETE ALL ----
@router.delete("/delete_all", response_model=MemoryResponse, status_code=status.HTTP_200_OK)
async def delete_all(
    use_case=Depends(get_semantic_memory_use_case),
):
    try:
        await use_case.delete_all()
        return MemoryResponse(message="all memory deleted")

    except Exception:
        logger.exception("[Semantic Memory Routes] delete_all failed")
        raise InternalServerException("Delete failed")


# ---- DROP TABLE ----
@router.delete("/drop_table", response_model=MemoryResponse, status_code=status.HTTP_200_OK)
async def drop_table(
    use_case=Depends(get_semantic_memory_use_case),
):
    try:
        result = await use_case.drop_table()

        if result:
            return MemoryResponse(message="semantic_memory table dropped successfully")

        return MemoryResponse(message="semantic_memory table does not exist")

    except Exception:
        logger.exception("[Semantic Memory Routes] drop_table failed")
        raise InternalServerException("Drop failed")