from fastapi import APIRouter
from health.endpoint import router

health_router = APIRouter()

health_router.include_router(router, prefix="")