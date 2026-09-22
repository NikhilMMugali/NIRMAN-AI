from fastapi import APIRouter

from app.api.v1.alerts import router as alerts_router
from app.api.v1.health import router as health_router
from app.api.v1.intelligence import router as intelligence_router
from app.api.v1.projects import router as projects_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="", tags=["health"])
api_router.include_router(projects_router, prefix="", tags=["projects"])
api_router.include_router(alerts_router, prefix="", tags=["alerts"])
api_router.include_router(intelligence_router, prefix="", tags=["intelligence"])
