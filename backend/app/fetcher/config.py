"""Configuration management for the Content Fetcher Service."""

import os
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_prefix="FETCHER_"
    )
    
    # Database configuration
    database_url: str = "sqlite:///./app.db"
    
    # Fetcher configuration
    concurrent_limit: int = 5
    request_delay: int = 1000  # milliseconds
    request_timeout: int = 30000  # milliseconds
    max_retries: int = 3
    user_agent: str = "NewsAgg/1.0 (Content Fetcher)"
    
    # Rate limiting
    min_domain_delay: int = 1000  # milliseconds between requests to same domain
    
    # Error handling
    max_consecutive_errors: int = 10  # auto-disable source after this many failures
    
    # Content extraction
    max_article_age_days: int = 365  # 1 year retention
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v):
        """Ensure database URL is properly formatted."""
        if not v:
            raise ValueError("DATABASE_URL cannot be empty")
        return v


# Global settings instance
settings = Settings()