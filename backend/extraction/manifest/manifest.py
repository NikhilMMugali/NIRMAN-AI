from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ExtractionManifestEntry:
    document: str
    status: str
    rows_extracted: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    processing_time_seconds: float = 0.0
    extracted_at: str = ""


class ExtractionManifest:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.entries: list[ExtractionManifestEntry] = []

    def add_entry(self, entry: ExtractionManifestEntry) -> None:
        self.entries.append(entry)

    def write(self) -> str:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(entry) for entry in self.entries]
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(self.path)
