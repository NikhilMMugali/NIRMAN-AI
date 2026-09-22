from fastapi import APIRouter
from app.repositories.supabase_repo import SupabaseRepository

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    supabase_repo = SupabaseRepository()
    supabase_status = supabase_repo.get_connection_status()

    return {
        "status": "ok",
        "service": "nirman-ai-api",
        "supabase": supabase_status,
    }
