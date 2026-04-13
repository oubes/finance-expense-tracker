# ---- Imports ----
import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.bootstrap.dependencies.memory_dep import get_memory_pipeline


# ---- Logger ----
logger = logging.getLogger(__name__)


# ---- Router ----
router = APIRouter()


# ---- Request Schema ----
class MemoryRequest(BaseModel):
    user_id: str
    user_input: str
    role: str


# ----------- Memory Pipeline -----------

@router.post("/run_memory_pipeline")
async def run_memory_pipeline(
    body: MemoryRequest,
    pipeline=Depends(get_memory_pipeline),
):
    logger.info("[API] start memory pipeline")

    result = await pipeline.run(
        user_input=body.user_input,
        user_id=body.user_id,
        role=body.role,
    )

    logger.info("[API] memory pipeline completed")

    return {
        "status": "success",
        "data": result,
    }