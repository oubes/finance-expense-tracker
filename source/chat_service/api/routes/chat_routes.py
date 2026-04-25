from fastapi import APIRouter, Response, status, Depends
from source.chat_service.core.di.dependencies import get_llm_service

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "up",
        "status_code": 200,
    }
    
@router.get("/llm/health")
async def llm_health_check(
    llm_service = Depends(get_llm_service),
):
    return await llm_service.health_check()

