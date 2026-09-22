from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from extraction.entity_resolution.resolver import EntityResolver
from extraction.manifest.manifest import ExtractionManifest, ExtractionManifestEntry
from extraction.normalization.normalizer import normalize_value
from extraction.readers.pdf_reader import PDFReader
from extraction.validation.validator import ExtractionValidator


class ExtractionPipeline:
    def __init__(self, input_path: str | Path) -> None:
        self.input_path = Path(input_path)
        self.reader = PDFReader()

    def run(self) -> dict[str, Any]:
        files = self._collect_files()
        root_dir = Path(__file__).resolve().parents[2]
        manifest_path = root_dir / "data" / "manifests" / "paimana_manifest.json"
        manifest = ExtractionManifest(manifest_path)

        processed_documents = 0
        successful_documents = 0
        failed_documents = 0
        extracted_records = 0

        for file_path in files:
            start = datetime.now(timezone.utc)
            try:
                rows = self._extract_project_rows(file_path)
                if rows:
                    extracted_values = rows
                else:
                    text, metadata = self.reader.read_text(file_path)
                    extracted_values = [self._build_record(file_path, text, metadata)]

                processed_documents += 1
                valid_rows = [row for row in extracted_values if ExtractionValidator.validate_record(row)["valid"]]
                if valid_rows:
                    successful_documents += 1
                    extracted_records += len(valid_rows)
                else:
                    failed_documents += 1

                manifest.add_entry(
                    ExtractionManifestEntry(
                        document=str(file_path),
                        status="success" if valid_rows else "warning",
                        rows_extracted=len(valid_rows),
                        errors=[] if valid_rows else ["no_valid_rows_extracted"],
                        warnings=[],
                        processing_time_seconds=(datetime.now(timezone.utc) - start).total_seconds(),
                        extracted_at=datetime.now(timezone.utc).isoformat(),
                    )
                )
            except Exception as exc:
                failed_documents += 1
                processed_documents += 1
                manifest.add_entry(
                    ExtractionManifestEntry(
                        document=str(file_path),
                        status="failed",
                        rows_extracted=0,
                        errors=[str(exc)],
                        warnings=[],
                        processing_time_seconds=(datetime.now(timezone.utc) - start).total_seconds(),
                        extracted_at=datetime.now(timezone.utc).isoformat(),
                    )
                )

        manifest.write()
        return {
            "documents_processed": processed_documents,
            "successful": successful_documents,
            "failed": failed_documents,
            "records_extracted": extracted_records,
            "manifest": str(manifest_path),
        }

    def _collect_files(self) -> list[Path]:
        if self.input_path.is_file() and self.input_path.suffix.lower() == ".zip":
            import tempfile
            import zipfile
            extract_dir = Path(tempfile.mkdtemp(prefix="nirman_zip_"))
            with zipfile.ZipFile(self.input_path, "r") as archive:
                for member in archive.infolist():
                    target_path = (extract_dir / member.filename).resolve()
                    if not target_path.is_relative_to(extract_dir.resolve()):
                        continue  # Protect against path traversal (Zip Slip)
                    if member.filename.lower().endswith(".pdf"):
                        archive.extract(member, extract_dir)
            return sorted(extract_dir.rglob("*.pdf"))
        if self.input_path.is_dir():
            return sorted(self.input_path.rglob("*.pdf"))
        if self.input_path.is_file() and self.input_path.suffix.lower() == ".pdf":
            return [self.input_path]
        return []

    @staticmethod
    def _parse_cost_values(raw: Any) -> tuple[float | None, float | None]:
        value = "" if raw is None else str(raw)
        if value == "" or value.lower() in {"na", "n.a.", "-"}:
            return None, None
        matches = re.findall(r"-?\d[\d,]*\.?\d*", value)
        numeric_values: list[float] = []
        for match in matches:
            cleaned = match.replace(",", "").strip()
            if cleaned and cleaned != "-":
                try:
                    numeric_values.append(float(cleaned))
                except ValueError:
                    continue
        if not numeric_values:
            return None, None
        original = numeric_values[0]
        revised = numeric_values[1] if len(numeric_values) > 1 and not re.search(r"\b(?:n\.a\.|na)\b", value, flags=re.IGNORECASE) else None
        return original, revised

    def _extract_project_rows(self, file_path: Path) -> list[dict[str, Any]]:
        try:
            import pdfplumber
        except Exception:
            return []

        file_path = Path(file_path)
        rows: list[dict[str, Any]] = []
        with pdfplumber.open(str(file_path)) as document:
            for page in document.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue
                    for row in table[1:]:
                        if not row:
                            continue
                        if len(row) < 9:
                            continue
                        project_name_cell = row[3] if len(row) > 3 else ""
                        if not project_name_cell or "Project Name" in str(project_name_cell):
                            continue
                        project_id = self._extract_project_id(project_name_cell)
                        project_name = self._clean_project_name(project_name_cell)
                        if not project_id or not project_name:
                            continue

                        cost_cell = row[6] if len(row) > 6 else None
                        orig_cost, rev_cost = self._parse_cost_values(cost_cell)

                        record = {
                            "project_id": project_id,
                            "project_name": project_name,
                            "original_cost": orig_cost,
                            "revised_cost": rev_cost,
                            "expenditure": normalize_value("expenditure", row[7] if len(row) > 7 else None),
                            "physical_progress": normalize_value("physical_progress", row[8] if len(row) > 8 else None),
                            "reporting_month": self._infer_reporting_month(file_path),
                            "source_file": str(file_path),
                            "file_hash": self.reader._sha256(file_path),
                            "source_page": page.page_number,
                            "extraction_confidence": 0.91,
                        }
                        rows.append(record)
        return rows

    def _build_record(self, file_path: Path, text: str, metadata: dict[str, Any]) -> dict[str, Any]:
        project_id = self._extract_field(text, ["PROJECT ID", "Project ID", "project_id"])
        project_name = self._extract_field(text, ["PROJECT NAME", "Project Name", "project_name"])
        original_cost = self._extract_field(text, ["ORIGINAL COST", "Original Cost", "original_cost"])
        revised_cost = self._extract_field(text, ["REVISED COST", "Revised Cost", "revised_cost"])
        expenditure = self._extract_field(text, ["EXPENDITURE", "CUMULATIVE EXPENDITURE", "expenditure"])
        physical_progress = self._extract_field(text, ["PHYSICAL PROGRESS", "Physical Progress", "physical_progress"])
        reporting_month = self._extract_field(text, ["REPORTING MONTH", "Reporting Month", "reporting_month"])

        record = {
            "project_id": project_id,
            "project_name": project_name,
            "original_cost": normalize_value("original_cost", original_cost),
            "revised_cost": normalize_value("revised_cost", revised_cost),
            "expenditure": normalize_value("expenditure", expenditure),
            "physical_progress": normalize_value("physical_progress", physical_progress),
            "reporting_month": reporting_month or self._infer_reporting_month(file_path),
            "source_file": str(file_path),
            "file_hash": metadata.get("file_hash"),
            "source_page": 1,
            "extraction_confidence": 0.9,
        }
        return record

    @staticmethod
    def _extract_field(text: str, aliases: list[str]) -> str | None:
        if not text:
            return None
        for alias in aliases:
            pattern = rf"(?:{re.escape(alias)})\s*[:\-\s]\s*([^\n\r]+)"
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                if val:
                    return val
        return None

    @staticmethod
    def _extract_project_id(project_name_cell: Any) -> str | None:
        if project_name_cell is None:
            return None
        match = re.search(r"\((N\d+)\)", str(project_name_cell), flags=re.IGNORECASE)
        return match.group(1) if match else None

    @staticmethod
    def _clean_project_name(project_name_cell: Any) -> str | None:
        if project_name_cell is None:
            return None
        value = str(project_name_cell)
        value = value.replace("\n", " ")
        value = re.sub(r"\s+", " ", value).strip()
        value = re.sub(r"\s*\([^)]*\)\s*$", "", value)
        value = re.sub(r"\s*\([^)]*\)\s*$", "", value)
        return value or None

    @staticmethod
    def _infer_reporting_month(file_path: Path) -> str | None:
        text = file_path.name
        month_map = {
            "January": "01", "February": "02", "March": "03", "April": "04", "May": "05",
            "June": "06", "July": "07", "August": "08", "September": "09", "October": "10",
            "November": "11", "December": "12",
        }
        for month_name, month_number in month_map.items():
            match = re.search(rf"{month_name}", text, flags=re.IGNORECASE)
            if match:
                year_match = re.search(r"(\d{4})", text[match.start():], flags=re.IGNORECASE)
                if year_match:
                    return f"{year_match.group(1)}-{month_number}"
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="PAIMANA extraction pipeline foundation")
    parser.add_argument("--input", dest="input_path", required=True, help="Input PDF directory or zip archive")
    parser.add_argument("--output", dest="output_path", default="../data/staging/paimana", help="Output directory")
    args = parser.parse_args()

    pipeline = ExtractionPipeline(args.input_path)
    result = pipeline.run()
    output = Path(args.output_path)
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
