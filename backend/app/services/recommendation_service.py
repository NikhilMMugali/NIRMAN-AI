from __future__ import annotations

from typing import Any


class PrototypeRecommendationEngine:
    """Deterministic, transparent government intervention recommendation engine for prototype evaluation."""

    def generate_recommendations(self, project_id: str, risk_data: dict[str, Any]) -> dict[str, Any]:
        risk_category = risk_data.get("risk_category", "LOW")
        probability = risk_data.get("risk_probability", 0.0)
        metrics = risk_data.get("metrics", {})

        progress = metrics.get("physical_progress_pct", 0.0)
        overrun = metrics.get("cost_overrun_pct", 0.0)
        stagnant = metrics.get("stagnant_months_3m", 0.0)
        gap = metrics.get("reporting_gap_months", 0.0)
        operational_status = risk_data.get("operational_status") or metrics.get("operational_status") or ("COMPLETED" if progress >= 100.0 else ("STAGNANT" if stagnant >= 2 else "IN_PROGRESS"))

        recommendations: list[dict[str, str]] = []

        if operational_status == "COMPLETED":
            if overrun > 5.0:
                recommendations.append({
                    "priority": "HIGH" if overrun > 10.0 else "MEDIUM",
                    "category": "POST_COMPLETION_AUDIT",
                    "action": "Conduct formal post-completion cost audit and financial reconciliation.",
                    "rationale": f"Project physically completed (100% progress) with cost overrun of {overrun}%.",
                })
            else:
                recommendations.append({
                    "priority": "LOW",
                    "category": "ROUTINE_CLOSURE",
                    "action": "Initiate routine project closure and asset handover proceedings.",
                    "rationale": "Project physically completed (100% progress) within acceptable budget parameters.",
                })
        else:
            # Rule 1: Progress Stagnation / Low Progress
            if stagnant >= 2 or progress < 50.0:
                recommendations.append({
                    "priority": "HIGH" if risk_category in ("HIGH", "CRITICAL") else "MEDIUM",
                    "category": "MILESTONE_RECOVERY",
                    "action": "Issue formal milestone recovery directive to project executive agency.",
                    "rationale": f"Physical progress has stagnated for {int(stagnant)} of the last 3 reporting periods (current progress: {progress}%).",
                })

            # Rule 2: Cost Overrun Exposure
            if overrun > 10.0:
                recommendations.append({
                    "priority": "HIGH",
                    "category": "FINANCIAL_AUDIT",
                    "action": "Trigger mandatory financial audit and revised cost estimate review by Ministry of Finance committee.",
                    "rationale": f"Revised cost exceeds original sanctioned budget by {overrun}%.",
                })
            elif overrun > 5.0:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "FINANCIAL_AUDIT",
                    "action": "Request cost variation justification and expenditure reconciliation statement.",
                    "rationale": f"Moderate cost overrun of {overrun}% detected above initial approval.",
                })

            # Rule 3: Reporting Gap / Data Quality
            if gap > 0:
                recommendations.append({
                    "priority": "MEDIUM",
                    "category": "REPORTING_COMPLIANCE",
                    "action": "Enforce mandatory monthly PAIMANA status updates from Nodal Officers.",
                    "rationale": f"Source submission delay of {int(gap)} month(s) creates reporting blindspot.",
                })

            # Default fallback for on-track active projects
            if not recommendations:
                recommendations.append({
                    "priority": "LOW",
                    "category": "ROUTINE_MONITORING",
                    "action": "Maintain routine monthly PAIMANA progress monitoring.",
                    "rationale": f"Project progress is tracking normally at {progress}% with zero budget overruns.",
                })

        return {
            "project_id": project_id,
            "engine": "PROTOTYPE_RULE_ENGINE",
            "risk_category": risk_category,
            "risk_probability": probability,
            "operational_status": operational_status,
            "count": len(recommendations),
            "recommendations": recommendations,
        }


recommendation_engine = PrototypeRecommendationEngine()
