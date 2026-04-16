from fastapi import APIRouter, Response, status

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "up",
        "status_code": 200,
    }