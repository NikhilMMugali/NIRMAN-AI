from __future__ import annotations

from typing import Any

from app.repositories.base_repo import BaseRepository


class AlertRepository(BaseRepository):
    def list_alerts(self) -> list[dict[str, Any]]:
        if not self.is_configured():
            return []
        return []
