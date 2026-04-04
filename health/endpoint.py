from fastapi import APIRouter, Response
from health.aggregator import get_readiness

router = APIRouter()


@router.get("/")
def health():
    return {"status": "alive"}


@router.get("/ready")
async def readiness(response: Response):
    return await get_readiness(response)