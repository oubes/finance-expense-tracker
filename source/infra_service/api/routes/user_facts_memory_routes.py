# ---- Imports ----
from fastapi import APIRouter, status, Depends, Body

from source.infra_service.api.models.user_facts_memory_model import (
    HealthCheckRequest,
    HealthCheckResponse,
    InitTableRequest,
    InitTableResponse,
    UpsertUserFactsRequest,
    UpsertUserFactsResponse,
    UpdateUserFactsRequest,
    UpdateUserFactsResponse,
    GetUserFactsRequest,
    GetUserFactsResponse,
    CountRequest,
    CountResponse,
    CountUserRequest,
    CountUserResponse,
    DeleteAllRequest,
    DeleteAllResponse,
    DropTableRequest,
    DropTableResponse,
    UserFactsOut,
)

from source.infra_service.core.di.dependencies import get_user_facts_use_case
from source.infra_service.core.errors.exceptions import (
    ValidationException,
    ServiceUnavailableException,
    InternalServerException,
)

import logging


# ---- Logger ----
logger = logging.getLogger(__name__)

router = APIRouter()


# ---- Health ----
@router.get("/health", response_model=HealthCheckResponse)
async def health(
    body: HealthCheckRequest = Body(default={}),
    use_case=Depends(get_user_facts_use_case),
):
    try:
        await use_case.health()
        return HealthCheckResponse(message="UserFacts service is up")

    except Exception:
        logger.exception("[UserFacts Routes] health failed")
        raise ServiceUnavailableException("UserFacts")


# ---- Init ----
@router.get("/init", response_model=InitTableResponse)
async def init(
    use_case=Depends(get_user_facts_use_case),
):
    try:
        already = await use_case.init()

        if already:
            return InitTableResponse(
                message="user_facts already initialized",
                status=status.HTTP_200_OK,
            )

        return InitTableResponse(
            message="user_facts initialized",
            status=status.HTTP_201_CREATED,
        )

    except Exception:
        logger.exception("[UserFacts Routes] init failed")
        raise InternalServerException("Init user_facts failed")


# ---- Upsert ----
@router.post("/upsert", response_model=UpsertUserFactsResponse)
async def upsert(
    body: UpsertUserFactsRequest,
    use_case=Depends(get_user_facts_use_case),
):
    if not body.data:
        raise ValidationException("data is required")

    try:
        d = body.data.model_dump()

        payload = (
            d.get("user_id"),
            d.get("income"),
            d.get("currency"),
            d.get("rent"),
            d.get("food_expense"),
            d.get("fixed_expenses"),
            d.get("disposable_income"),
        )

        await use_case.upsert(payload)

        return UpsertUserFactsResponse(
            message="User facts upserted (added or updated)"
        )

    except Exception:
        logger.exception("[UserFacts Routes] upsert failed")
        raise InternalServerException("Upsert user facts failed")


# ---- Update ----
@router.patch("/update/{user_id}", response_model=UpdateUserFactsResponse)
async def update(
    user_id: str,
    body: UpdateUserFactsRequest,
    use_case=Depends(get_user_facts_use_case),
):
    if not body.data:
        raise ValidationException("data is required")

    try:
        d = body.data.model_dump(exclude_unset=True)

        payload = (
            d.get("income"),
            d.get("currency"),
            d.get("rent"),
            d.get("food_expense"),
            d.get("fixed_expenses"),
            d.get("disposable_income"),
            user_id,
        )

        await use_case.update(payload)

        return UpdateUserFactsResponse(message="User facts updated")

    except Exception:
        logger.exception("[UserFacts Routes] update failed")
        raise InternalServerException("Update user facts failed")


# ---- Get ----
@router.post("/get", response_model=GetUserFactsResponse)
async def get_user_facts(
    body: GetUserFactsRequest,
    use_case=Depends(get_user_facts_use_case),
):
    if not body.user_id:
        raise ValidationException("user_id required")

    try:
        row = await use_case.get_user_facts(body.user_id)

        result = UserFactsOut.model_validate(row) if row else None

        return GetUserFactsResponse(result=result)

    except Exception:
        logger.exception("[UserFacts Routes] get_user_facts failed")
        raise InternalServerException("Get user facts failed")


# ---- Count ----
@router.post("/count", response_model=CountResponse)
async def count(
    body: CountRequest = Body(default={}),
    use_case=Depends(get_user_facts_use_case),
):
    try:
        count = await use_case.count()

        return CountResponse(
            count=count,
            message=f"Total rows: {count}",
        )

    except Exception:
        logger.exception("[UserFacts Routes] count failed")
        raise InternalServerException("Count failed")


# ---- Count Per User ----
@router.post("/count_user", response_model=CountUserResponse)
async def count_user(
    body: CountUserRequest,
    use_case=Depends(get_user_facts_use_case),
):
    if not body.user_id:
        raise ValidationException("user_id required")

    try:
        count = await use_case.count_user(body.user_id)

        return CountUserResponse(
            count=count,
            message=f"User rows: {count}",
        )

    except Exception:
        logger.exception("[UserFacts Routes] count_user failed")
        raise InternalServerException("Count user failed")


# ---- Delete All ----
@router.delete("/delete_all", response_model=DeleteAllResponse)
async def delete_all(
    body: DeleteAllRequest = Body(default={}),
    use_case=Depends(get_user_facts_use_case),
):
    try:
        await use_case.delete_all()
        return DeleteAllResponse(message="All user facts deleted")

    except Exception:
        logger.exception("[UserFacts Routes] delete failed")
        raise InternalServerException("Delete failed")


# ---- Drop ----
@router.delete("/drop", response_model=DropTableResponse)
async def drop(
    body: DropTableRequest = Body(default={}),
    use_case=Depends(get_user_facts_use_case),
):
    try:
        result = await use_case.drop_table()

        if result:
            return DropTableResponse(message="user_facts dropped")

        return DropTableResponse(message="user_facts does not exist")

    except Exception:
        logger.exception("[UserFacts Routes] drop failed")
        raise InternalServerException("Drop failed")