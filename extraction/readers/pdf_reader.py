from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


class PDFReader:
    """Read PDF text with optional third-party support and graceful fallback."""

    def __init__(self) -> None:
        self._reader_impl = self._resolve_reader()

    def _resolve_reader(self) -> Any:
        for module_name in ("pypdf", "PyPDF2", "fitz", "pdfplumber"):
            try:
                return __import__(module_name)
            except Exception:
                continue
        return None

    @staticmethod
    def _sha256(path: str | Path) -> str:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def read_text(self, file_path: str | Path) -> tuple[str, dict[str, Any]]:
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        metadata = {"source_file": str(file_path), "file_hash": self._sha256(file_path)}

        if self._reader_impl is None:
            return "", {**metadata, "method": "unavailable", "content_preview": ""}

        try:
            if self._reader_impl.__name__ == "fitz":
                document = self._reader_impl.open(str(file_path))
                pages = [page.get_text("text") for page in document]
                text = "\n".join(page for page in pages if page)
                return text, {**metadata, "method": "fitz", "page_count": len(pages)}

            if self._reader_impl.__name__ in {"pypdf", "PyPDF2"}:
                reader = self._reader_impl.PdfReader(str(file_path))
                pages = [page.extract_text() or "" for page in reader.pages]
                text = "\n".join(page for page in pages if page)
                return text, {**metadata, "method": self._reader_impl.__name__, "page_count": len(pages)}

            if self._reader_impl.__name__ == "pdfplumber":
                with self._reader_impl.open(str(file_path)) as document:
                    pages = [page.extract_text() or "" for page in document.pages]
                    text = "\n".join(page for page in pages if page)
                    return text, {**metadata, "method": "pdfplumber", "page_count": len(pages)}
        except Exception:
            return "", {**metadata, "method": "failed", "content_preview": ""}

        return "", {**metadata, "method": "unsupported", "content_preview": ""}
