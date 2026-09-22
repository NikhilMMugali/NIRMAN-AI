from __future__ import annotations

from typing import Any, Protocol


class DatabaseClient(Protocol):
    def query(self, query: str, *args: Any, **kwargs: Any) -> Any:
        ...


class BaseRepository:
    def __init__(self, db_client: DatabaseClient | None = None) -> None:
        self.db_client = db_client

    def is_configured(self) -> bool:
        return self.db_client is not None
