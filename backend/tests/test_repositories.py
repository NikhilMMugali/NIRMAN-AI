from app.repositories.projects_repo import ProjectRepository
from app.repositories.status_repo import ProjectStatusRepository


def test_project_repository_returns_empty_list_when_unconfigured() -> None:
    repo = ProjectRepository(db_client=None, use_local_fallback=False)

    assert repo.list_projects() == []
    assert repo.get_by_id("nonexistent-project-id-123456") is None


def test_status_repository_builds_month_key() -> None:
    repo = ProjectStatusRepository(db_client=None)

    assert repo.unique_project_month_key("project-123", "2025-01") == "project-123|2025-01"
