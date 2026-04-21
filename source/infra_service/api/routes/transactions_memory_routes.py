# ---- Imports ----
import logging
from fastapi import APIRouter, Depends, status

from source.infra_service.core.di.dependencies import get_transactions_use_case
from source.infra_service.api.models.transactions_memory_model import (
    AddTransactionRequest,
    BM25SearchRequest,
    VectorSearchRequest,
    HybridSearchRequest,
    SearchResponse,
    MemoryResponse,
)

from source.infra_service.core.errors.exceptions import (
    ValidationException,
    InternalServerException,
    ServiceUnavailableException,
)

# ---- Logger ----
logger = logging.getLogger(__name__)

router = APIRouter()


# ---- HEALTH CHECK (mapped to init check) ----
@router.get("/health", status_code=status.HTTP_200_OK)
async def health(
    use_case=Depends(get_transactions_use_case),
):
    try:
        await use_case.init()
        return {"message": "Transactions service is up"}

    except Exception:
        logger.exception("[Transactions Routes] health check failed - service unreachable")
        raise ServiceUnavailableException("Transactions")


# ---- INIT TABLE ----
@router.get("/init", response_model=MemoryResponse)
async def init(
    use_case=Depends(get_transactions_use_case),
):
    try:
        already_initialized = await use_case.init()

        if already_initialized:
            return MemoryResponse(message="Transactions table already initialized and ready")

        return MemoryResponse(message="Transactions table initialized successfully")

    except Exception:
        logger.exception("[Transactions Routes] init failed - database setup error")
        raise InternalServerException("Failed to initialize transactions table")


# ---- COUNT ROWS ----
@router.get("/count")
async def count(
    use_case=Depends(get_transactions_use_case),
):
    try:
        value = await use_case.count_rows()

        return {
            "count": value,
            "message": f"Total transaction records in system: {value}"
        }

    except Exception:
        logger.exception("[Transactions Routes] count failed - unable to fetch stats")
        raise InternalServerException("Failed to count transactions")


# ---- ADD TRANSACTION ----
@router.post("/add", response_model=MemoryResponse)
async def add(
    body: AddTransactionRequest,
    use_case=Depends(get_transactions_use_case),
):
    try:
        if not body.user_id or not body.session_id or not body.raw_input:
            raise ValidationException("user_id, session_id and raw_input are required for transaction logging")

        data = (
            body.user_id,
            body.session_id,
            body.product,
            body.category,
            body.amount,
            body.quantity,
            body.currency,
            body.note,
            body.raw_input,
            body.embedding,
        )

        ok = await use_case.log_event(data)

        if not ok:
            raise InternalServerException("Transaction insert operation failed")

        return MemoryResponse(message="Transaction successfully recorded")

    except Exception:
        logger.exception("[Transactions Routes] add failed - transaction insert error")
        raise InternalServerException("Failed to add transaction")


# ---- HISTORY (NOT AVAILABLE IN USECASE - REMOVED SAFE FALLBACK) ----
@router.post("/history", response_model=SearchResponse)
async def history(
    body: dict,
):
    raise InternalServerException("History endpoint not implemented in current use case")


# ---- CATEGORY (NOT AVAILABLE IN USECASE - REMOVED SAFE FALLBACK) ----
@router.post("/category", response_model=SearchResponse)
async def category(
    body: dict,
):
    raise InternalServerException("Category endpoint not implemented in current use case")


# ---- BM25 SEARCH ----
@router.post("/search/bm25", response_model=SearchResponse)
async def bm25(
    body: BM25SearchRequest,
    use_case=Depends(get_transactions_use_case),
):
    try:
        res = await use_case.bm25_search(
            body.user_id,
            body.session_id,
            body.query,
            body.limit,
        )

        return SearchResponse(count=len(res), results=res)

    except Exception:
        logger.exception("[Transactions Routes] bm25 failed - lexical search error")
        raise InternalServerException("BM25 search failed")


# ---- VECTOR SEARCH ----
@router.post("/search/vector", response_model=SearchResponse)
async def vector(
    body: VectorSearchRequest,
    use_case=Depends(get_transactions_use_case),
):
    try:
        res = await use_case.vector_search(
            body.user_id,
            body.session_id,
            body.embedding,
            body.limit,
        )

        return SearchResponse(count=len(res), results=res)

    except Exception:
        logger.exception("[Transactions Routes] vector failed - embedding search error")
        raise InternalServerException("Vector search failed")


# ---- HYBRID SEARCH ----
@router.post("/search/hybrid", response_model=SearchResponse)
async def hybrid(
    body: HybridSearchRequest,
    use_case=Depends(get_transactions_use_case),
):
    try:
        res = await use_case.hybrid_search(
            body.user_id,
            body.session_id,
            body.query,
            body.embedding,
            body.limit,
            body.weights,
        )

        return SearchResponse(count=len(res), results=res)

    except Exception:
        logger.exception("[Transactions Routes] hybrid failed - fusion search error")
        raise InternalServerException("Hybrid search failed")


# ---- DELETE ALL ----
@router.delete("/delete_all", response_model=MemoryResponse)
async def delete_all(
    use_case=Depends(get_transactions_use_case),
):
    try:
        deleted = await use_case.delete_all()
        if deleted:
            return MemoryResponse(message="All transaction records permanently deleted")
        else:
            table_exists = await use_case.db.execute_one(use_case.q.HEALTH_CHECK)
            if not table_exists or not table_exists.get("to_regclass"):
                return MemoryResponse(message="Transactions table does not exist.")
            else:
                return MemoryResponse(message="No records to delete. Transactions table is already empty.")

    except Exception:
        logger.exception("[Transactions Routes] delete_all failed - destructive operation error")
        raise InternalServerException("Failed to delete all transactions")


# ---- DROP TABLE ----
@router.delete("/drop_table", response_model=MemoryResponse)
async def drop_table(
    use_case=Depends(get_transactions_use_case),
):
    try:
        result = await use_case.drop_table()

        if result:
            return MemoryResponse(message="Transactions table dropped successfully from database")

        return MemoryResponse(message="Transactions table does not exist - nothing to drop")

    except Exception:
        logger.exception("[Transactions Routes] drop_table failed - schema destruction error")
        raise InternalServerException("Failed to drop transactions table")