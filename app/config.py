from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AutoHeal DevOps Agent"
    environment: str = "development"
    log_level: str = "INFO"

    # Gemini API credentials — loaded from .env locally, GitHub Secrets in CI
    gemini_api_key: Optional[str] = None

    # Gemini model configuration — change here to switch models project-wide
    # Free tier recommended: gemini-2.5-flash
    # Complex analysis: gemini-2.5-pro
    gemini_default_model: str = "gemini-2.5-flash"
    gemini_complex_model: str = "gemini-2.5-pro"

    # GitHub integration settings
    github_token: Optional[str] = None
    github_repository: Optional[str] = None

    # CORS configuration
    allowed_origins_raw: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins_raw.split(",") if origin.strip()]


settings = Settings()
