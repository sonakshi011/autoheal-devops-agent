from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "AutoHeal DevOps Agent"
    environment: str = "development"
    log_level: str = "INFO"
    gemini_api_key: Optional[str] = None
    github_token: Optional[str] = None
    github_repository: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()
