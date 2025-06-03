from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "sqlite:///./app.db"
    postgres_server: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_db: Optional[str] = None
    
    secret_key: str = "your-secret-key-here"
    
    # Content fetching settings
    fetch_interval_hours: int = 1
    max_sources: int = 100
    article_retention_days: int = 365
    
    class Config:
        env_file = ".env"

settings = Settings()