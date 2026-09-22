from fastapi import APIRouter

router = APIRouter()


@router.get("/sectors")
async def list_sectors() -> dict:
    return {
        "success": False,
        "message": "Sector intelligence is not yet available.",
        "data": [],
    }


@router.get("/states")
async def list_states() -> dict:
    return {
        "success": False,
        "message": "State intelligence is not yet available.",
        "data": [],
    }
