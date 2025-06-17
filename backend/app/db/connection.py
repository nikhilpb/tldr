"""Database connection and engine management."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool
import logging

logger = logging.getLogger(__name__)

# Base class for database models
Base = declarative_base()


def create_database_engine(database_url: str):
    """Create database engine with proper configuration for SQLite and PostgreSQL."""
    
    if database_url.startswith("sqlite"):
        # SQLite configuration for development
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False  # Set to True for SQL debugging
        )
    else:
        # PostgreSQL configuration for production
        engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False  # Set to True for SQL debugging
        )
    
    return engine


def create_database_tables(engine):
    """Create all database tables. Used for initial setup."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def test_database_connection(engine) -> bool:
    """
    Test database connectivity.
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False 