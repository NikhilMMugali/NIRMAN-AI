from pathlib import Path

from extraction.normalization.normalizer import normalize_currency, normalize_percentage
from extraction.pipeline import ExtractionPipeline
from extraction.validation.validator import ExtractionValidator


def test_pipeline_extracts_real_project_row_from_paimana_pdf() -> None:
    pdf_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "paimana" / "zip" / "FRFebruary2025.pdf"
    pipeline = ExtractionPipeline(pdf_path)
    rows = pipeline._extract_project_rows(pdf_path)

    assert rows, "expected at least one extracted project row from the real PDF table"
    row = next((item for item in rows if item["project_id"] == "N04000073"), None)
    assert row is not None, "expected the known N04000073 record to be present in the parsed PDF rows"
    assert "CONSTRUCTION OF NEW INTEGRATED TERMINAL BUILDING" in row["project_name"]
    assert row["reporting_month"] == "2025-02"
    assert row["original_cost"] == 417.23
    assert row["physical_progress"] == 100.0


def test_normalize_currency_handles_indian_currency_strings() -> None:
    assert normalize_currency("₹ 108,000 crore") == 108000.0


def test_normalize_percentage_handles_percentage_values() -> None:
    assert normalize_percentage("62.16%") == 62.16


def test_extraction_validator_flags_missing_project_fields() -> None:
    result = ExtractionValidator.validate_record({"project_name": "Example"})
    assert result["valid"] is False
    assert "missing_project_id" in result["issues"]


def test_extraction_validator_accepts_zero_progress() -> None:
    result = ExtractionValidator.validate_record({
        "project_id": "P123",
        "project_name": "Test Project",
        "physical_progress": 0.0,
    })
    assert result["valid"] is True, "valid zero physical progress must not be flagged as missing or invalid"


def test_extract_field_returns_parsed_value_not_alias() -> None:
    text = "ORIGINAL COST : 568.92 Crore\nPROJECT NAME: Test Airport"
    value = ExtractionPipeline._extract_field(text, ["ORIGINAL COST", "Original Cost"])
    assert value == "568.92 Crore", f"expected '568.92 Crore', got '{value}'"


def test_pdf_reader_raises_clean_file_not_found() -> None:
    from extraction.readers.pdf_reader import PDFReader
    import pytest

    reader = PDFReader()
    non_existent = Path("/tmp/does_not_exist_123456.pdf")
    with pytest.raises(FileNotFoundError) as exc_info:
        reader.read_text(non_existent)
    assert "Document not found" in str(exc_info.value)

