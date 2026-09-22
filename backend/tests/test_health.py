from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "nirman-ai-api"
    # Supabase status block is present when credentials are configured
    assert "supabase" in body
    assert body["supabase"]["service"] == "supabase"


def test_config_has_default_app_name() -> None:
    from app.core.config import get_settings

    settings = get_settings()
    assert settings.app_name == "nirman-ai-api"


def test_missing_dependency_handler_is_safe() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_missing_route_returns_structured_error() -> None:
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"] == {"code": 404, "message": "Not Found"}
