"""Tests for database connection and session management."""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.fetcher.database import (
    create_database_engine, 
    get_database_session, 
    create_database_tables,
    test_database_connection
)
from app.fetcher.config import Settings


class TestDatabaseEngine:
    """Tests for database engine creation."""
    
    def test_sqlite_engine_creation(self):
        """Test SQLite engine creation with proper configuration."""
        with patch('app.fetcher.database.settings') as mock_settings:
            mock_settings.database_url = "sqlite:///./test.db"
            
            engine = create_database_engine()
            
            assert engine is not None
            assert "sqlite" in str(engine.url)
    
    def test_postgresql_engine_creation(self):
        """Test PostgreSQL engine creation with proper configuration."""
        with patch('app.fetcher.database.settings') as mock_settings:
            mock_settings.database_url = "postgresql://user:pass@localhost/testdb"
            
            engine = create_database_engine()
            
            assert engine is not None
            assert "postgresql" in str(engine.url)


class TestDatabaseSession:
    """Tests for database session management."""
    
    def test_get_database_session(self):
        """Test database session creation and cleanup."""
        with patch('app.fetcher.database.SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            
            # Test successful session
            sessions = list(get_database_session())
            
            assert len(sessions) == 1
            assert sessions[0] == mock_session
            mock_session.close.assert_called_once()
    
    def test_get_database_session_with_exception(self):
        """Test database session cleanup on exception."""
        with patch('app.fetcher.database.SessionLocal') as mock_session_local:
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            
            # Test that session.close() is called even when exception occurs
            generator = get_database_session()
            session = next(generator)
            
            try:
                # Simulate an exception
                raise Exception("Test exception")
            except Exception:
                # Complete the generator to trigger cleanup
                try:
                    next(generator)
                except StopIteration:
                    pass
            
            # Verify close was called (rollback is called in the real exception handler)
            mock_session.close.assert_called_once()


class TestDatabaseOperations:
    """Tests for database operations."""
    
    @patch('app.fetcher.database.Base.metadata.create_all')
    @patch('app.fetcher.database.engine')
    def test_create_database_tables_success(self, mock_engine, mock_create_all):
        """Test successful database table creation."""
        mock_create_all.return_value = None
        
        # Should not raise an exception
        create_database_tables()
        
        mock_create_all.assert_called_once_with(bind=mock_engine)
    
    @patch('app.fetcher.database.Base.metadata.create_all')
    @patch('app.fetcher.database.engine')
    def test_create_database_tables_failure(self, mock_engine, mock_create_all):
        """Test database table creation failure."""
        mock_create_all.side_effect = SQLAlchemyError("Table creation failed")
        
        with pytest.raises(SQLAlchemyError):
            create_database_tables()
    
    @patch('app.fetcher.database.engine')
    def test_database_connection_success(self, mock_engine):
        """Test successful database connection test."""
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        
        result = test_database_connection()
        
        assert result is True
        # Verify execute was called (the text() wrapper will be used internally)
        mock_connection.execute.assert_called_once()
    
    @patch('app.fetcher.database.engine')
    def test_database_connection_failure(self, mock_engine):
        """Test database connection test failure."""
        mock_engine.connect.side_effect = SQLAlchemyError("Connection failed")
        
        result = test_database_connection()
        
        assert result is False