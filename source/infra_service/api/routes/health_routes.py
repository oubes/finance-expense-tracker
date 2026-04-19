from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def health_check():
    return {
        "status": "up",
        "status_code": 200,
    }
    