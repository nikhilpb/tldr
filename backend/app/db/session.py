"""Database session management utilities."""

from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

logger = logging.getLogger(__name__)


def get_database_session(session_local) -> Generator[Session, None, None]:
    """
    Create a database session for dependency injection.
    
    Args:
        session_local: SessionLocal factory
        
    Yields:
        Session: SQLAlchemy database session
    """
    session = session_local()
    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close() 