# ---- Imports ----
from fastapi import APIRouter, Response
from src.core.health.aggregator import get_readiness

# ---- Router Initialization ----
router = APIRouter()


# ---- Liveness Endpoint ----
@router.get("/")
def health():
    return {"status": "alive"}


# ---- Readiness Endpoint ----
@router.get("/ready")
async def readiness(response: Response):
    return await get_readiness(response)