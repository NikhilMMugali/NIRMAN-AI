from app.core.config import Settings, get_settings


def test_settings_default_values() -> None:
    settings = Settings()
    assert settings.app_name == "nirman-ai-api"
    assert settings.api_prefix == "/api/v1"


def test_get_settings_is_cached() -> None:
    settings_1 = get_settings()
    settings_2 = get_settings()
    assert settings_1 is settings_2
