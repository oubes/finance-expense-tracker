# ---- Imports ----
from pydantic import BaseModel
from datetime import datetime


# ---- Base ----
class UserFactsBase(BaseModel):
    user_id: str
    income: float | None = None
    currency: str = "EGP"
    rent: float | None = None
    food_expense: float | None = None
    fixed_expenses: float | None = None
    disposable_income: float | None = None
    created_at: datetime | None = None


# ---- Schemas ----
class UserFactsIn(UserFactsBase):
    pass


class UserFactsUpdate(BaseModel):
    income: float | None = None
    currency: str | None = None
    rent: float | None = None
    food_expense: float | None = None
    fixed_expenses: float | None = None
    disposable_income: float | None = None


class UserFactsOut(UserFactsBase):
    id: int


# ---- Health ----
class HealthCheckRequest(BaseModel):
    pass


class HealthCheckResponse(BaseModel):
    message: str


# ---- Init ----
class InitTableRequest(BaseModel):
    pass


class InitTableResponse(BaseModel):
    message: str
    status: int


# ---- Upsert ----
class UpsertUserFactsRequest(BaseModel):
    data: UserFactsIn


class UpsertUserFactsResponse(BaseModel):
    message: str


# ---- Update ----
class UpdateUserFactsRequest(BaseModel):
    data: UserFactsUpdate


class UpdateUserFactsResponse(BaseModel):
    message: str


# ---- Get ----
class GetUserFactsResponse(BaseModel):
    result: UserFactsOut | None


# ---- Count ----
class CountResponse(BaseModel):
    count: int
    message: str

# ---- Delete All ----
class DeleteAllRequest(BaseModel):
    pass


class DeleteAllResponse(BaseModel):
    message: str


# ---- Drop ----
class DropTableRequest(BaseModel):
    pass


class DropTableResponse(BaseModel):
    message: str