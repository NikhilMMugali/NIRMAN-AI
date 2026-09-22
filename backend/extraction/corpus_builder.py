from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw" / "paimana" / "zip"
CURATED_DIR = ROOT_DIR / "data" / "curated" / "paimana"
MANIFEST_DIR = ROOT_DIR / "data" / "manifests"
VALIDATION_DIR = ROOT_DIR / "data" / "validation"


@dataclass
class DocumentReport:
    document_id: str
    file_path: str
    sha256: str
    page_count: int
    report_type: str
    reporting_year: int | None
    reporting_month: int | None
    extraction_method: str
    status: str
    extracted_row_count: int
    warnings: list[str]
    failures: list[str]


class PAIMANACorpusBuilder:
    def __init__(self, raw_dir: str | Path = RAW_DIR) -> None:
        self.raw_dir = Path(raw_dir)
        self.curated_dir = CURATED_DIR
        self.manifest_dir = MANIFEST_DIR
        self.validation_dir = VALIDATION_DIR
        self.curated_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_dir.mkdir(parents=True, exist_ok=True)
        self.validation_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _clean_text(value: Any) -> str:
        if value is None:
            return ""
        text = str(value).replace("\n", " ")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _infer_period_from_filename(file_name: str) -> tuple[int | None, int | None]:
        explicit_match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)[^\d]*(\d{4})", file_name, flags=re.IGNORECASE)
        if explicit_match:
            month_name = explicit_match.group(1).title()
            year = int(explicit_match.group(2))
            month_number = {
                "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
                "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
            }[month_name]
            return year, month_number

        month_match = re.search(r"(?:FR|FlashReport|Report|Review_Report|Flash_Report)\s*(January|February|March|April|May|June|July|August|September|October|November|December)[^\d]*(\d{4})", file_name, flags=re.IGNORECASE)
        if month_match:
            month_name = month_match.group(1).title()
            year = int(month_match.group(2))
            month_number = {
                "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
                "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
            }[month_name]
            return year, month_number

        month_name_match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)", file_name, flags=re.IGNORECASE)
        if month_name_match:
            month_name = month_name_match.group(1).title()
            year_match = re.search(r"(\d{4})", file_name[month_name_match.start():], flags=re.IGNORECASE)
            if year_match:
                year = int(year_match.group(1))
                month_number = {
                    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
                    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
                }[month_name]
                return year, month_number
        return None, None

    @staticmethod
    def _parse_cost_values(raw: Any) -> tuple[float | None, float | None, float | None]:
        value = "" if raw is None else str(raw)
        if value == "" or value.lower() in {"na", "n.a.", "-"}:
            return None, None, None
        matches = re.findall(r"-?\d[\d,]*\.?\d*(?:\s*crore)?", value, flags=re.IGNORECASE)
        numeric_values: list[float] = []
        for match in matches:
            cleaned = match.replace(",", "").replace("₹", "").replace("Crore", "").replace("crore", "").replace("Cr", "").replace("cr", "").strip()
            if cleaned and cleaned != "-":
                try:
                    numeric_values.append(float(cleaned))
                except ValueError:
                    continue
        if not numeric_values:
            return None, None, None
        original = numeric_values[0]
        revised = numeric_values[1] if len(numeric_values) > 1 and not re.search(r"\b(?:n\.a\.|na)\b", value, flags=re.IGNORECASE) else None
        anticipated = numeric_values[2] if len(numeric_values) > 2 else (numeric_values[1] if revised is None and len(numeric_values) > 1 else None)
        return original, revised, anticipated

    @staticmethod
    def _parse_currency_value(raw: Any) -> float | None:
        if raw is None:
            return None
        text = str(raw).strip()
        if not text or text.lower() in {"na", "n.a.", "-"}:
            return None
        text = text.replace("₹", "").replace("Crore", "").replace("crore", "").replace("Cr", "").replace("cr", "").replace(",", "").strip()
        matches = re.findall(r"-?\d+\.?\d*", text)
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                return None
        return None

    @staticmethod
    def _parse_percentage(raw: Any) -> float | None:
        if raw is None:
            return None
        text = str(raw).strip()
        if not text or text.lower() in {"na", "n.a.", "-"}:
            return None
        text = text.replace("%", "").replace(",", "")
        try:
            value = float(text)
            return value
        except ValueError:
            return None

    @staticmethod
    def _extract_project_id(cell: Any) -> str | None:
        if cell is None:
            return None
        match = re.search(r"\((N\d+)\)", str(cell), flags=re.IGNORECASE)
        if match:
            return match.group(1)
        match = re.search(r"\b(N\d{5,})\b", str(cell), flags=re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _clean_project_name(cell: Any) -> str | None:
        if cell is None:
            return None
        value = str(cell)
        value = value.replace("\n", " ")
        value = re.sub(r"\s+", " ", value).strip()
        value = re.sub(r"\s*\([^)]*\)\s*$", "", value)
        value = re.sub(r"\s*\([^)]*\)\s*$", "", value)
        return value or None

    @staticmethod
    def _infer_report_type(file_name: str) -> str:
        lowered = file_name.lower()
        if "review" in lowered:
            return "review_report"
        if "flash" in lowered:
            return "flash_report"
        if "fr" in lowered and "january" in lowered:
            return "flash_report"
        return "unknown_report"

    def _extract_rows_from_pdf(self, pdf_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        rows: list[dict[str, Any]] = []
        warnings: list[str] = []
        failures: list[str] = []
        try:
            import pdfplumber

            document_hash = self._sha256(pdf_path)
            year, month = self._infer_period_from_filename(pdf_path.name)
            reporting_period = f"{year}-{month:02d}" if (year and month) else None

            with pdfplumber.open(str(pdf_path)) as document:
                for page_no, page in enumerate(document.pages, start=1):
                    tables = page.extract_tables()
                    for table in tables:
                        if not table:
                            continue
                        header_idx = None
                        for i, r in enumerate(table[:4]):
                            if r and any(k in str(cell or "").lower() for cell in r for k in ["project name", "name of project", "project_name", "name of the project", "project (id)"]):
                                header_idx = i
                                break
                        start_row = header_idx + 1 if header_idx is not None else 0

                        for row in table[start_row:]:
                            if not row or len(row) < 7:
                                continue
                            
                            # Find project_id & name across potential columns
                            project_id = None
                            project_name = None
                            project_name_cell = ""
                            
                            for idx in [3, 2, 1, 0, 4]:
                                if len(row) > idx and row[idx]:
                                    cell_str = str(row[idx])
                                    pid = self._extract_project_id(cell_str)
                                    if pid:
                                        project_id = pid
                                        project_name_cell = cell_str
                                        project_name = self._clean_project_name(cell_str)
                                        break
                            
                            if not project_id or not project_name:
                                continue

                            state = row[0] if len(row) > 0 else None
                            sector = row[1] if len(row) > 1 else None
                            cost_raw = row[6] if len(row) > 6 else (row[5] if len(row) > 5 else None)
                            expenditure_raw = row[7] if len(row) > 7 else None
                            progress_raw = row[8] if len(row) > 8 else (row[-1] if len(row) > 8 else None)
                            
                            original_cost, revised_cost, anticipated_cost = self._parse_cost_values(cost_raw)
                            expenditure = self._parse_currency_value(expenditure_raw)
                            progress = self._parse_percentage(progress_raw)
                            rows.append(
                                {
                                    "project_id": project_id,
                                    "project_name": project_name,
                                    "state": self._clean_text(state),
                                    "sector": self._clean_text(sector),
                                    "original_cost_raw": self._clean_text(cost_raw),
                                    "original_cost": original_cost,
                                    "revised_cost_raw": self._clean_text(cost_raw),
                                    "revised_cost": revised_cost,
                                    "anticipated_cost_raw": self._clean_text(cost_raw),
                                    "anticipated_cost": anticipated_cost,
                                    "expenditure_raw": self._clean_text(expenditure_raw),
                                    "expenditure": expenditure,
                                    "physical_progress_raw": self._clean_text(progress_raw),
                                    "physical_progress": progress,
                                    "reporting_year": year,
                                    "reporting_month": month,
                                    "reporting_period": reporting_period,
                                    "source_pdf": str(pdf_path.relative_to(ROOT_DIR)) if pdf_path.is_relative_to(ROOT_DIR) else str(pdf_path),
                                    "source_page": page_no,
                                    "document_id": pdf_path.stem,
                                    "file_hash": document_hash,
                                    "extraction_method": "pdfplumber",
                                    "source_table": "project_table",
                                    "project_status": "observed",
                                }
                            )
        except Exception as exc:  # pragma: no cover
            failures.append(str(exc))

        if not rows:
            warnings.append("no_project_rows_extracted")
        return rows, [{"file": str(pdf_path), "warnings": warnings, "failures": failures}]

    def build(self) -> dict[str, Any]:
        documents: list[DocumentReport] = []
        all_rows: list[dict[str, Any]] = []
        for pdf_path in sorted(self.raw_dir.glob("*.pdf")):
            rows, errors = self._extract_rows_from_pdf(pdf_path)
            all_rows.extend(rows)
            year, month = self._infer_period_from_filename(pdf_path.name)
            flattened_warnings: list[str] = []
            flattened_failures: list[str] = []
            for item in errors:
                for warning in item.get("warnings", []):
                    flattened_warnings.append(str(warning))
                for failure in item.get("failures", []):
                    flattened_failures.append(str(failure))
            document_report = DocumentReport(
                document_id=pdf_path.stem,
                file_path=str(pdf_path),
                sha256=self._sha256(pdf_path),
                page_count=0,
                report_type=self._infer_report_type(pdf_path.name),
                reporting_year=year,
                reporting_month=month,
                extraction_method="pdfplumber",
                status="success" if rows else "warning",
                extracted_row_count=len(rows),
                warnings=flattened_warnings,
                failures=flattened_failures,
            )
            try:
                import pdfplumber

                with pdfplumber.open(str(pdf_path)) as handle:
                    document_report.page_count = len(handle.pages)
            except Exception:
                pass
            documents.append(document_report)

        df = pd.DataFrame(all_rows)
        duplicate_rows = pd.DataFrame()
        if not df.empty:
            duplicate_mask = df.duplicated(subset=["project_id", "reporting_period"], keep=False)
            duplicate_rows = df.loc[duplicate_mask].sort_values(["project_id", "reporting_period", "source_pdf"])
        duplicate_rows.to_csv(self.curated_dir / "project_monthly_status_duplicates.csv", index=False)
        project_monthly = df.copy()
        key_cols = ["project_id", "reporting_period"]
        if not project_monthly.empty:
            project_monthly = project_monthly.drop_duplicates(subset=key_cols, keep="last")
            project_monthly = project_monthly.sort_values(["reporting_period", "project_id"]).reset_index(drop=True)

        if project_monthly.empty:
            project_summary = pd.DataFrame(
                columns=[
                    "project_id", "project_name", "state", "sector",
                    "first_reporting_period", "latest_reporting_period", "observations",
                ]
            )
        else:
            project_summary = project_monthly.groupby("project_id", as_index=False).agg(
                project_name=("project_name", "first"),
                state=("state", "last"),
                sector=("sector", "last"),
                first_reporting_period=("reporting_period", "min"),
                latest_reporting_period=("reporting_period", "max"),
                observations=("project_id", "size"),
            )

        curated_dir = self.curated_dir
        project_monthly.to_csv(curated_dir / "project_monthly_status.csv", index=False)
        project_monthly.to_parquet(curated_dir / "project_monthly_status.parquet", index=False)
        project_summary.to_csv(curated_dir / "projects.csv", index=False)
        project_summary.to_parquet(curated_dir / "projects.parquet", index=False)

        quality_rows = []
        for doc in documents:
            quality_rows.append(
                {
                    "document_id": doc.document_id,
                    "source_pdf": doc.file_path,
                    "sha256": doc.sha256,
                    "report_type": doc.report_type,
                    "reporting_year": doc.reporting_year,
                    "reporting_month": doc.reporting_month,
                    "page_count": doc.page_count,
                    "extraction_method": doc.extraction_method,
                    "status": doc.status,
                    "extracted_row_count": doc.extracted_row_count,
                    "warnings": "; ".join(str(item) for item in doc.warnings),
                    "failures": "; ".join(str(item) for item in doc.failures),
                }
            )
        quality_df = pd.DataFrame(quality_rows)
        quality_df.to_csv(curated_dir / "extraction_quality.csv", index=False)
        quality_df.to_parquet(curated_dir / "extraction_quality.parquet", index=False)

        profile = {
            "documents_total": len(documents),
            "documents_processed": len([d for d in documents if d.status in {"success", "warning"}]),
            "documents_failed": len([d for d in documents if d.status == "failed"]),
            "unique_projects": int(project_summary["project_id"].nunique()) if not project_summary.empty else 0,
            "project_month_observations": int(len(project_monthly)) if not project_monthly.empty else 0,
            "duplicate_project_period_count": int(len(df) - len(project_monthly)) if not df.empty else 0,
            "duplicate_project_period_rows_reviewed": int(len(duplicate_rows)),
            "reporting_range": {
                "earliest": min(project_monthly["reporting_period"]) if not project_monthly.empty else None,
                "latest": max(project_monthly["reporting_period"]) if not project_monthly.empty else None,
            },
            "field_coverage": {
                "project_id": float(project_monthly["project_id"].notna().mean()) if not project_monthly.empty else 0.0,
                "project_name": float(project_monthly["project_name"].notna().mean()) if not project_monthly.empty else 0.0,
                "state": float(project_monthly["state"].notna().mean()) if not project_monthly.empty else 0.0,
                "sector": float(project_monthly["sector"].notna().mean()) if not project_monthly.empty else 0.0,
                "original_cost": float(project_monthly["original_cost"].notna().mean()) if not project_monthly.empty else 0.0,
                "expenditure": float(project_monthly["expenditure"].notna().mean()) if not project_monthly.empty else 0.0,
                "physical_progress": float(project_monthly["physical_progress"].notna().mean()) if not project_monthly.empty else 0.0,
            },
        }

        with (self.manifest_dir / "PAIMANA_DATASET_PROFILE.json").open("w", encoding="utf-8") as handle:
            json.dump(profile, handle, indent=2)

        golden_records = project_monthly.head(20).copy()
        golden_records.to_csv(self.validation_dir / "paimana_golden_records.csv", index=False)

        markdown = [
            "# PAIMANA Dataset Profile",
            "",
            f"- Total PDFs: {profile['documents_total']}",
            f"- Processed PDFs: {profile['documents_processed']}",
            f"- Failed PDFs: {profile['documents_failed']}",
            f"- Unique projects: {profile['unique_projects']}",
            f"- Project-month observations: {profile['project_month_observations']}",
            f"- Duplicate project-period count: {profile['duplicate_project_period_count']}",
            f"- Duplicate rows preserved for review: {profile['duplicate_project_period_rows_reviewed']}",
            f"- Reporting range: {profile['reporting_range']['earliest']} to {profile['reporting_range']['latest']}",
            "",
            "## Field coverage",
        ]
        for name, coverage in profile["field_coverage"].items():
            markdown.append(f"- {name}: {coverage:.2%}")
        (self.manifest_dir / "PAIMANA_DATASET_PROFILE.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")

        return {
            "documents_total": len(documents),
            "documents_processed": len([d for d in documents if d.status in {"success", "warning"}]),
            "documents_failed": len([d for d in documents if d.status == "failed"]),
            "project_month_observations": int(len(project_monthly)) if not project_monthly.empty else 0,
            "unique_projects": int(project_summary["project_id"].nunique()) if not project_summary.empty else 0,
            "duplicate_project_period_count": int(len(df) - len(project_monthly)) if not df.empty else 0,
            "project_monthly_path": str(curated_dir / "project_monthly_status.csv"),
        }


def main() -> None:
    builder = PAIMANACorpusBuilder()
    result = builder.build()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
