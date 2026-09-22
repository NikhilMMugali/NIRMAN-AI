from __future__ import annotations

from typing import Any


class ExtractionValidator:
    @staticmethod
    def has_required_fields(record: dict[str, Any], required_fields: list[str]) -> list[str]:
        missing = [
            field for field in required_fields
            if record.get(field) is None or str(record.get(field)).strip() == ""
        ]
        return missing

    @staticmethod
    def validate_project_id(project_id: Any) -> bool:
        return bool(project_id is not None and str(project_id).strip())

    @staticmethod
    def validate_percent(value: Any) -> bool:
        if value is None:
            return False
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return False
        return 0.0 <= numeric <= 100.0

    @staticmethod
    def validate_record(record: dict[str, Any]) -> dict[str, Any]:
        issues: list[str] = []
        for field in ("project_id", "project_name"):
            val = record.get(field)
            if val is None or str(val).strip() == "":
                issues.append(f"missing_{field}")
        if "physical_progress" in record and record.get("physical_progress") is not None:
            if not ExtractionValidator.validate_percent(record.get("physical_progress")):
                issues.append("invalid_physical_progress")
        if "cost_risk" in record and record.get("cost_risk") is not None:
            if not ExtractionValidator.validate_percent(record.get("cost_risk")):
                issues.append("invalid_cost_risk")
        return {"valid": not issues, "issues": issues}
