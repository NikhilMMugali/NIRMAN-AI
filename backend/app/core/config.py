from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "nirman-ai-api"
    environment: str = "development"
    debug: bool = False

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_value(cls, v: object) -> bool:
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "debug", "dev")
        return bool(v)
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    gemini_api_key: str = ""
    groq_api_key: str = ""
    llm_provider: str = ""

    database_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_allowlist(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
