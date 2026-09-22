from __future__ import annotations

from typing import Any


class EntityResolver:
    @staticmethod
    def resolve_project(record: dict[str, Any]) -> dict[str, Any]:
        project_id = record.get("project_id")
        project_name = record.get("project_name")
        if project_id:
            return {"project_key": str(project_id), "match_confidence": 1.0, "review_required": False}
        if project_name:
            return {"project_key": str(project_name), "match_confidence": 0.5, "review_required": True}
        return {"project_key": None, "match_confidence": 0.0, "review_required": True}
