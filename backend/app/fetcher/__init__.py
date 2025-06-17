"""Content Fetcher Service for the News Aggregator."""

from sqlalchemy.orm import sessionmaker

from .config import settings
from ..db import (
    create_database_engine, 
    create_database_tables as _create_database_tables,
    test_database_connection as _test_database_connection,
    get_database_session as _get_database_session,
    Base
)
from ..models import Source, Article
from .runner import FetcherRunner

# Create fetcher-specific database engine and session factory
engine = create_database_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_database_session():
    """Get database session for fetcher service."""
    yield from _get_database_session(SessionLocal)

def create_database_tables():
    """Create all database tables for fetcher service."""
    _create_database_tables(engine)

def test_database_connection():
    """Test database connection for fetcher service."""
    return _test_database_connection(engine)

__all__ = [
    "settings",
    "create_database_tables", 
    "test_database_connection",
    "get_database_session",
    "engine",
    "SessionLocal",
    "Base",
    "Source",
    "Article",
    "FetcherRunner"
]