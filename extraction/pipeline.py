from __future__ import annotations

import argparse
import json
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
        manifest_path = Path("data/manifests") / "paimana_manifest.json"
        manifest = ExtractionManifest(manifest_path)

        processed_documents = 0
        successful_documents = 0
        failed_documents = 0
        extracted_records = 0

        for file_path in files:
            start = datetime.now(timezone.utc)
            try:
                text, metadata = self.reader.read_text(file_path)
                record = self._build_record(file_path, text, metadata)
                validation = ExtractionValidator.validate_record(record)
                entity = EntityResolver.resolve_project(record)
                processed_documents += 1
                if validation["valid"]:
                    successful_documents += 1
                    extracted_records += 1
                else:
                    failed_documents += 1
                manifest.add_entry(
                    ExtractionManifestEntry(
                        document=str(file_path),
                        status="success" if validation["valid"] else "warning",
                        rows_extracted=1 if validation["valid"] else 0,
                        errors=[] if validation["valid"] else validation["issues"],
                        warnings=["entity_review_required"] if entity["review_required"] else [],
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
                        continue
                    if member.filename.lower().endswith(".pdf"):
                        archive.extract(member, extract_dir)
            return sorted(extract_dir.rglob("*.pdf"))
        if self.input_path.is_dir():
            return sorted(self.input_path.rglob("*.pdf"))
        if self.input_path.is_file() and self.input_path.suffix.lower() == ".pdf":
            return [self.input_path]
        return []

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
            "reporting_month": reporting_month,
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
        import re
        for alias in aliases:
            pattern = rf"(?:{re.escape(alias)})\s*[:\-\s]\s*([^\n\r]+)"
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                if val:
                    return val
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="PAIMANA extraction pipeline foundation")
    parser.add_argument("--input", dest="input_path", required=True, help="Input PDF directory or zip archive")
    parser.add_argument("--output", dest="output_path", default="data/staging/paimana", help="Output directory")
    args = parser.parse_args()

    pipeline = ExtractionPipeline(args.input_path)
    result = pipeline.run()
    output = Path(args.output_path)
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
