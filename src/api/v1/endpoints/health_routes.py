from fastapi import APIRouter
from src.core.health.endpoint import router as health_router

router = APIRouter()

router.include_router(health_router)