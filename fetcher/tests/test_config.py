"""Tests for configuration management."""

import pytest
import os
from pydantic import ValidationError

from app.config import Settings


class TestSettings:
    """Tests for the Settings configuration class."""
    
    def test_default_settings(self):
        """Test default configuration values."""
        settings = Settings()
        
        assert settings.database_url == "sqlite:///./app.db"
        assert settings.concurrent_limit == 5
        assert settings.request_delay == 1000
        assert settings.request_timeout == 30000
        assert settings.max_retries == 3
        assert settings.user_agent == "NewsAgg/1.0 (Content Fetcher)"
        assert settings.min_domain_delay == 1000
        assert settings.max_consecutive_errors == 10
        assert settings.max_article_age_days == 365
    
    def test_environment_variable_override(self, monkeypatch):
        """Test that environment variables override defaults."""
        # Set environment variables with FETCHER_ prefix
        monkeypatch.setenv("FETCHER_DATABASE_URL", "postgresql://test:test@localhost/testdb")
        monkeypatch.setenv("FETCHER_CONCURRENT_LIMIT", "10")
        monkeypatch.setenv("FETCHER_REQUEST_DELAY", "2000")
        monkeypatch.setenv("FETCHER_MAX_RETRIES", "5")
        monkeypatch.setenv("FETCHER_USER_AGENT", "TestAgent/2.0")
        
        settings = Settings()
        
        assert settings.database_url == "postgresql://test:test@localhost/testdb"
        assert settings.concurrent_limit == 10
        assert settings.request_delay == 2000
        assert settings.max_retries == 5
        assert settings.user_agent == "TestAgent/2.0"
    
    def test_database_url_validation(self):
        """Test database URL validation."""
        # Test empty database URL
        with pytest.raises(ValidationError):
            Settings(database_url="")
        
        # Test valid URLs
        valid_urls = [
            "sqlite:///./test.db",
            "postgresql://user:pass@localhost/db",
            "mysql://user:pass@localhost/db"
        ]
        
        for url in valid_urls:
            settings = Settings(database_url=url)
            assert settings.database_url == url
    
    def test_type_conversion(self, monkeypatch):
        """Test that environment variables are properly converted to correct types."""
        monkeypatch.setenv("FETCHER_CONCURRENT_LIMIT", "15")
        monkeypatch.setenv("FETCHER_REQUEST_DELAY", "3000")
        monkeypatch.setenv("FETCHER_MAX_ARTICLE_AGE_DAYS", "180")
        
        settings = Settings()
        
        assert isinstance(settings.concurrent_limit, int)
        assert isinstance(settings.request_delay, int)
        assert isinstance(settings.max_article_age_days, int)
        assert settings.concurrent_limit == 15
        assert settings.request_delay == 3000
        assert settings.max_article_age_days == 180