from fastapi import APIRouter
from core.health.endpoint import router as health_router

health_router = APIRouter()

health_router.include_router(health_router)