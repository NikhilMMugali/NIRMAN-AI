from fastapi import APIRouter

router = APIRouter()


@router.get("/alerts")
async def list_alerts() -> dict:
    return {
        "success": False,
        "message": "Alert data is not yet available.",
        "data": [],
    }
