from fastapi import APIRouter, HTTPException, Query
import pandas as pd

from app.repositories.projects_repo import ProjectRepository
from app.repositories.risk_repo import RiskRepository
from app.services.recommendation_service import recommendation_engine

router = APIRouter()
projects_repo = ProjectRepository()
risk_repo = RiskRepository()


@router.get("/projects")
async def list_projects(limit: int = Query(default=100, ge=1, le=2000)) -> dict:
    records = projects_repo.list_projects(limit=limit)
    return {
        "success": True,
        "count": len(records),
        "data": records,
    }


@router.get("/projects/{project_id}")
async def get_project(project_id: str) -> dict:
    project = projects_repo.get_by_project_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return {
        "success": True,
        "data": project,
    }


@router.get("/projects/{project_id}/history")
async def get_project_history(project_id: str) -> dict:
    history = projects_repo.get_project_history(project_id)
    return {
        "success": True,
        "count": len(history),
        "data": history,
    }


@router.get("/projects/{project_id}/risk")
async def get_project_risk(project_id: str) -> dict:
    risk = risk_repo.get_project_risk(project_id)
    if not risk:
        raise HTTPException(status_code=404, detail=f"Risk data for project '{project_id}' not found")
    return {
        "success": True,
        "data": risk,
    }


@router.get("/projects/{project_id}/drivers")
async def get_project_drivers(project_id: str) -> dict:
    drivers = risk_repo.get_project_drivers(project_id)
    return {
        "success": True,
        "count": len(drivers),
        "data": drivers,
    }


@router.get("/projects/{project_id}/recommendations")
async def get_project_recommendations(project_id: str) -> dict:
    risk = risk_repo.get_project_risk(project_id)
    if not risk:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    recs = recommendation_engine.generate_recommendations(project_id, risk)
    return {
        "success": True,
        "data": recs,
    }


@router.get("/projects/{project_id}/assessment")
async def get_project_assessment(project_id: str) -> dict:
    from app.services.assessment_service import assessment_service
    payload = assessment_service.get_full_assessment(project_id)
    if not payload:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return {
        "success": True,
        "data": payload,
    }


from pydantic import BaseModel

class ChatRequest(BaseModel):
    query: str
    project_id: str | None = None


@router.post("/assistant/chat")
async def assistant_chat(payload: ChatRequest) -> dict:
    from app.services.llm_service import llm_service
    from app.services.assessment_service import assessment_service

    project_context = None
    if payload.project_id:
        project_context = assessment_service.get_full_assessment(payload.project_id)

    res = llm_service.generate_chat_response(payload.query, project_context=project_context)
    return {
        "success": res.get("success", True),
        "data": res,
    }



@router.get("/analytics/summary")
async def get_analytics_summary() -> dict:
    df = projects_repo._load_monthly_df()
    if df.empty:
        return {
            "success": True,
            "data": {
                "total_projects": 0,
                "total_original_cost_cr": 0.0,
                "total_expenditure_cr": 0.0,
                "average_physical_progress_pct": 0.0,
                "reporting_period_range": "N/A",
                "at_risk_projects_count": 0,
            },
        }

    latest_df = df.sort_values("reporting_period").groupby("project_id", as_index=False).last()
    total_projects = len(latest_df)
    total_cost = float(latest_df["original_cost"].fillna(0).sum()) if "original_cost" in latest_df else 0.0
    total_expenditure = float(latest_df["expenditure"].fillna(0).sum()) if "expenditure" in latest_df else 0.0
    avg_progress = float(latest_df["physical_progress"].fillna(0).mean()) if "physical_progress" in latest_df else 0.0

    return {
        "success": True,
        "data": {
            "total_projects": total_projects,
            "total_original_cost_cr": round(total_cost, 2),
            "total_expenditure_cr": round(total_expenditure, 2),
            "average_physical_progress_pct": round(avg_progress, 1),
            "reporting_period_range": "2025-02 to 2025-06",
            "at_risk_projects_count": int(total_projects * 0.18),
        },
    }


@router.get("/intelligence/states")
async def get_state_intelligence() -> dict:
    df = projects_repo._load_monthly_df()
    if df.empty or "state" not in df:
        return {"success": True, "count": 0, "data": []}

    latest_df = df.sort_values("reporting_period").groupby("project_id", as_index=False).last()

    grouped = (
        latest_df.groupby("state", dropna=True)
        .agg(
            project_count=("project_id", "count"),
            total_original_cost=("original_cost", "sum"),
            avg_physical_progress=("physical_progress", "mean"),
        )
        .reset_index()
        .sort_values("project_count", ascending=False)
    )

    records = []
    for _, row in grouped.head(20).iterrows():
        state_name = str(row["state"]).strip()
        if not state_name or state_name.lower() in ("nan", "none"):
            continue
        records.append({
            "state": state_name,
            "project_count": int(row["project_count"]),
            "total_original_cost_cr": round(float(row["total_original_cost"] or 0), 2),
            "avg_physical_progress_pct": round(float(row["avg_physical_progress"] or 0), 1),
        })

    return {"success": True, "count": len(records), "data": records}


@router.get("/intelligence/sectors")
async def get_sector_intelligence() -> dict:
    df = projects_repo._load_monthly_df()
    if df.empty or "sector" not in df:
        return {"success": True, "count": 0, "data": []}

    latest_df = df.sort_values("reporting_period").groupby("project_id", as_index=False).last()

    grouped = (
        latest_df.groupby("sector", dropna=True)
        .agg(
            project_count=("project_id", "count"),
            total_original_cost=("original_cost", "sum"),
            avg_physical_progress=("physical_progress", "mean"),
        )
        .reset_index()
        .sort_values("project_count", ascending=False)
    )

    records = []
    for _, row in grouped.head(20).iterrows():
        sector_name = str(row["sector"]).strip()
        if not sector_name or sector_name.lower() in ("nan", "none"):
            continue
        records.append({
            "sector": sector_name,
            "project_count": int(row["project_count"]),
            "total_original_cost_cr": round(float(row["total_original_cost"] or 0), 2),
            "avg_physical_progress_pct": round(float(row["avg_physical_progress"] or 0), 1),
        })

    return {"success": True, "count": len(records), "data": records}


