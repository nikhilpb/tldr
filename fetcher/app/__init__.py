"""Content Fetcher Service for News Aggregator App."""

__version__ = "1.0.0"
__description__ = "Service for fetching and processing news content from RSS feeds and websites"

# Import core components for easy access
from .config import settings
from .database import get_database_session, create_database_tables, test_database_connection
from .models import Source, Article

__all__ = [
    "settings",
    "get_database_session", 
    "create_database_tables",
    "test_database_connection",
    "Source",
    "Article"
]