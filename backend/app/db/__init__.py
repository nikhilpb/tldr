"""Shared database package for the News Aggregator application."""

# Import and re-export from dedicated modules
from .connection import (
    Base,
    create_database_engine,
    create_database_tables,
    test_database_connection
)
from .session import get_database_session

# Export all database utilities
__all__ = [
    "Base",
    "create_database_engine", 
    "create_database_tables",
    "test_database_connection",
    "get_database_session"
] 