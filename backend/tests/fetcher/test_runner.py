"""Unit tests for FetcherRunner class."""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.fetcher.runner import FetcherRunner
from app.fetcher.models import Source, Article
from app.fetcher.database import Base


@pytest.fixture
def test_db_session():
    """Create a test database session."""
    # Use in-memory SQLite for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_sources():
    """Create mock Source objects for testing."""
    source1 = Mock(spec=Source)
    source1.id = 1
    source1.name = "Test RSS Feed 1"
    source1.url = "https://test1.com/rss.xml"
    source1.type = "rss"
    source1.is_active = True
    
    source2 = Mock(spec=Source)
    source2.id = 2
    source2.name = "Test RSS Feed 2"
    source2.url = "https://test2.com/rss.xml"
    source2.type = "rss"
    source2.is_active = True
    
    source3 = Mock(spec=Source)
    source3.id = 3
    source3.name = "Test Website"
    source3.url = "https://test3.com"
    source3.type = "website"
    source3.is_active = True
    
    return [source1, source2, source3]


@pytest.fixture
def sample_articles():
    """Create sample article data for testing."""
    return [
        {
            "title": "Test Article 1",
            "url": "https://test1.com/article1",
            "author": "John Doe",
            "published_at": datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "summary": "This is test article 1",
            "content": "Full content of test article 1"
        },
        {
            "title": "Test Article 2",
            "url": "https://test1.com/article2",
            "author": "Jane Smith",
            "published_at": datetime(2023, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            "summary": "This is test article 2",
            "content": "Full content of test article 2"
        }
    ]


@pytest.fixture
def runner():
    """Create FetcherRunner instance for testing."""
    with patch('app.fetcher.runner.RSSFetcher'):
        return FetcherRunner()


class TestFetcherRunner:
    """Test suite for FetcherRunner class."""
    
    def test_init(self, runner):
        """Test FetcherRunner initialization."""
        assert runner.rss_fetcher is not None
    
    @patch('app.fetcher.runner.settings')
    @patch('app.fetcher.runner.RSSFetcher')
    def test_init_with_settings(self, mock_rss_fetcher, mock_settings):
        """Test FetcherRunner initialization with settings."""
        mock_settings.request_timeout = 30000
        mock_settings.user_agent = "Test Agent"
        
        runner = FetcherRunner()
        
        mock_rss_fetcher.assert_called_once_with(
            timeout=30,  # 30000ms converted to 30s
            user_agent="Test Agent"
        )
    
    def test_get_active_sources_success(self, runner, mock_sources):
        """Test successful retrieval of active sources."""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_sources
        
        result = runner.get_active_sources(mock_session)
        
        mock_session.query.assert_called_once_with(Source)
        mock_query.filter.assert_called_once()
        mock_query.all.assert_called_once()
        assert result == mock_sources
    
    def test_get_active_sources_database_error(self, runner):
        """Test handling database error when retrieving sources."""
        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception, match="Database connection failed"):
            runner.get_active_sources(mock_session)
    
    def test_fetch_articles_from_source_rss(self, runner, mock_sources, sample_articles):
        """Test fetching articles from RSS source."""
        rss_source = mock_sources[0]  # First source is RSS
        runner.rss_fetcher.fetch_articles.return_value = sample_articles
        
        result = runner.fetch_articles_from_source(rss_source)
        
        runner.rss_fetcher.fetch_articles.assert_called_once_with(rss_source)
        assert result == sample_articles
    
    def test_fetch_articles_from_source_website(self, runner, mock_sources):
        """Test fetching articles from website source (not implemented)."""
        website_source = mock_sources[2]  # Third source is website
        
        result = runner.fetch_articles_from_source(website_source)
        
        assert result == []
    
    def test_fetch_articles_from_source_unsupported_type(self, runner):
        """Test fetching from unsupported source type."""
        unsupported_source = Mock(spec=Source)
        unsupported_source.type = "unknown"
        
        with pytest.raises(ValueError, match="Unsupported source type: unknown"):
            runner.fetch_articles_from_source(unsupported_source)
    
    def test_fetch_articles_from_source_rss_error(self, runner, mock_sources):
        """Test handling RSS fetcher error."""
        rss_source = mock_sources[0]
        runner.rss_fetcher.fetch_articles.side_effect = Exception("RSS fetch failed")
        
        with pytest.raises(Exception, match="RSS fetch failed"):
            runner.fetch_articles_from_source(rss_source)
    
    @patch('app.fetcher.runner.logger')
    def test_log_fetch_results_success(self, mock_logger, runner, mock_sources, sample_articles):
        """Test logging successful fetch results."""
        source = mock_sources[0]
        
        runner.log_fetch_results(source, sample_articles)
        
        mock_logger.info.assert_called_once_with(
            f"Successfully fetched {len(sample_articles)} articles from source '{source.name}' (ID: {source.id})"
        )
    
    @patch('app.fetcher.runner.logger')
    def test_log_fetch_results_error(self, mock_logger, runner, mock_sources):
        """Test logging fetch error results."""
        source = mock_sources[0]
        error = Exception("Fetch failed")
        
        runner.log_fetch_results(source, [], error=error)
        
        mock_logger.error.assert_called_once_with(
            f"Failed to fetch from source '{source.name}' (ID: {source.id}): Fetch failed"
        )
    
    @patch('app.fetcher.runner.logger')
    def test_log_fetch_results_debug_mode(self, mock_logger, runner, mock_sources, sample_articles):
        """Test logging with debug mode enabled."""
        mock_logger.isEnabledFor.return_value = True
        source = mock_sources[0]
        
        runner.log_fetch_results(source, sample_articles)
        
        # Should log info message and debug messages for first 3 articles
        expected_calls = [
            call(f"Successfully fetched {len(sample_articles)} articles from source '{source.name}' (ID: {source.id})"),
        ]
        mock_logger.info.assert_has_calls(expected_calls)
        
        # Should log debug messages for articles
        assert mock_logger.debug.call_count == 2  # Two articles
    
    @patch('app.fetcher.runner.settings')
    def test_update_source_fetch_status_success(self, mock_settings, runner, mock_sources):
        """Test updating source status after successful fetch."""
        mock_settings.max_consecutive_errors = 10
        mock_session = Mock()
        source = mock_sources[0]
        
        runner.update_source_fetch_status(mock_session, source, success=True)
        
        source.update_fetch_success.assert_called_once_with(mock_session)
    
    @patch('app.fetcher.runner.settings')
    def test_update_source_fetch_status_error(self, mock_settings, runner, mock_sources):
        """Test updating source status after fetch error."""
        mock_settings.max_consecutive_errors = 10
        mock_session = Mock()
        source = mock_sources[0]
        error_message = "Fetch failed"
        
        runner.update_source_fetch_status(mock_session, source, success=False, error_message=error_message)
        
        source.update_fetch_error.assert_called_once_with(mock_session, error_message, max_errors=10)
    
    @patch('app.fetcher.runner.settings')
    def test_update_source_fetch_status_error_no_message(self, mock_settings, runner, mock_sources):
        """Test updating source status with no error message."""
        mock_settings.max_consecutive_errors = 10
        mock_session = Mock()
        source = mock_sources[0]
        
        runner.update_source_fetch_status(mock_session, source, success=False)
        
        source.update_fetch_error.assert_called_once_with(mock_session, "Unknown error", max_errors=10)
    
    @patch('app.fetcher.runner.logger')
    def test_update_source_fetch_status_exception(self, mock_logger, runner, mock_sources):
        """Test handling exception during source status update."""
        mock_session = Mock()
        source = mock_sources[0]
        source.update_fetch_success.side_effect = Exception("Update failed")
        
        runner.update_source_fetch_status(mock_session, source, success=True)
        
        mock_logger.error.assert_called_once_with(f"Error updating source {source.id} fetch status: Update failed")
    
    @patch('app.fetcher.runner.get_database_session')
    @patch('app.fetcher.runner.logger')
    def test_run_fetch_cycle_success(self, mock_logger, mock_get_session, runner, mock_sources, sample_articles):
        """Test successful fetch cycle execution."""
        # Setup mock session
        mock_session = Mock()
        mock_session_gen = Mock()
        mock_session_gen.__next__ = Mock(side_effect=[mock_session, StopIteration])
        mock_get_session.return_value = mock_session_gen
        
        # Setup mock sources query
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_sources[:2]  # Only RSS sources
        
        # Setup mock RSS fetcher
        runner.rss_fetcher.fetch_articles.return_value = sample_articles
        
        runner.run_fetch_cycle()
        
        # Verify logging
        mock_logger.info.assert_any_call("Starting fetch cycle")
        mock_logger.info.assert_any_call("Found 2 active sources in database")
        mock_logger.info.assert_any_call("Fetch cycle completed:")
        mock_logger.info.assert_any_call("  Sources processed: 2")
        mock_logger.info.assert_any_call("  Sources failed: 0")
        mock_logger.info.assert_any_call("  Total articles fetched: 4")  # 2 sources * 2 articles each
    
    @patch('app.fetcher.runner.get_database_session')
    @patch('app.fetcher.runner.logger')
    def test_run_fetch_cycle_no_sources(self, mock_logger, mock_get_session, runner):
        """Test fetch cycle with no active sources."""
        # Setup mock session
        mock_session = Mock()
        mock_session_gen = Mock()
        mock_session_gen.__next__ = Mock(side_effect=[mock_session, StopIteration])
        mock_get_session.return_value = mock_session_gen
        
        # Setup empty sources query
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        runner.run_fetch_cycle()
        
        mock_logger.warning.assert_called_once_with("No active sources found in database")
    
    @patch('app.fetcher.runner.get_database_session')
    @patch('app.fetcher.runner.logger')
    def test_run_fetch_cycle_with_errors(self, mock_logger, mock_get_session, runner, mock_sources):
        """Test fetch cycle with some source errors."""
        # Setup mock session
        mock_session = Mock()
        mock_session_gen = Mock()
        mock_session_gen.__next__ = Mock(side_effect=[mock_session, StopIteration])
        mock_get_session.return_value = mock_session_gen
        
        # Setup mock sources query
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_sources[:2]  # Only RSS sources
        
        # Setup mock RSS fetcher with error for first source
        runner.rss_fetcher.fetch_articles.side_effect = [
            Exception("Fetch failed for source 1"),
            [{"title": "Article", "url": "https://test.com/article"}]
        ]
        
        runner.run_fetch_cycle()
        
        # Verify logging includes error information
        mock_logger.info.assert_any_call("  Sources processed: 2")
        mock_logger.info.assert_any_call("  Sources failed: 1")
        mock_logger.info.assert_any_call("  Total articles fetched: 1")
    
    @patch('app.fetcher.runner.get_database_session')
    @patch('app.fetcher.runner.logger')
    def test_run_fetch_cycle_fatal_error(self, mock_logger, mock_get_session, runner):
        """Test fetch cycle with fatal error."""
        # Setup mock session that throws exception
        mock_session = Mock()
        mock_session_gen = Mock()
        mock_session_gen.__next__ = Mock(side_effect=[mock_session, StopIteration])
        mock_get_session.return_value = mock_session_gen
        
        # Simulate fatal error in get_active_sources
        mock_session.query.side_effect = Exception("Database connection lost")
        
        with pytest.raises(Exception, match="Database connection lost"):
            runner.run_fetch_cycle()
        
        mock_logger.error.assert_called_with("Fatal error during fetch cycle: Database connection lost")
    
    @patch('app.fetcher.runner.get_database_session')
    @patch('app.fetcher.runner.logger')
    def test_run_single_source_success(self, mock_logger, mock_get_session, runner, sample_articles):
        """Test successful single source fetch."""
        source_id = 1
        
        # Setup mock session
        mock_session = Mock()
        mock_session_gen = Mock()
        mock_session_gen.__next__ = Mock(side_effect=[mock_session, StopIteration])
        mock_get_session.return_value = mock_session_gen
        
        # Setup mock source query
        mock_source = Mock(spec=Source)
        mock_source.id = source_id
        mock_source.name = "Test Source"
        mock_source.type = "rss"
        mock_source.is_active = True
        
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_source
        
        # Setup mock RSS fetcher
        runner.rss_fetcher.fetch_articles.return_value = sample_articles
        
        runner.run_single_source(source_id)
        
        mock_logger.info.assert_any_call(f"Running fetch for single source ID: {source_id}")
        runner.rss_fetcher.fetch_articles.assert_called_once_with(mock_source)
        mock_source.update_fetch_success.assert_called_once_with(mock_session)
    
    @patch('app.fetcher.runner.get_database_session')
    @patch('app.fetcher.runner.logger')
    def test_run_single_source_not_found(self, mock_logger, mock_get_session, runner):
        """Test single source fetch with non-existent source."""
        source_id = 999
        
        # Setup mock session
        mock_session = Mock()
        mock_session_gen = Mock()
        mock_session_gen.__next__ = Mock(side_effect=[mock_session, StopIteration])
        mock_get_session.return_value = mock_session_gen
        
        # Setup mock source query that returns None
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        runner.run_single_source(source_id)
        
        mock_logger.error.assert_called_with(f"Source with ID {source_id} not found")
    
    @patch('app.fetcher.runner.get_database_session')
    @patch('app.fetcher.runner.logger')
    def test_run_single_source_inactive(self, mock_logger, mock_get_session, runner):
        """Test single source fetch with inactive source."""
        source_id = 1
        
        # Setup mock session
        mock_session = Mock()
        mock_session_gen = Mock()
        mock_session_gen.__next__ = Mock(side_effect=[mock_session, StopIteration])
        mock_get_session.return_value = mock_session_gen
        
        # Setup mock inactive source
        mock_source = Mock(spec=Source)
        mock_source.id = source_id
        mock_source.is_active = False
        
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_source
        
        runner.run_single_source(source_id)
        
        mock_logger.warning.assert_called_with(f"Source {source_id} is not active")
    
    @patch('app.fetcher.runner.get_database_session')
    @patch('app.fetcher.runner.logger')
    @patch('app.fetcher.runner.settings')
    def test_run_single_source_fetch_error(self, mock_settings, mock_logger, mock_get_session, runner):
        """Test single source fetch with fetch error."""
        mock_settings.max_consecutive_errors = 10
        source_id = 1
        
        # Setup mock session
        mock_session = Mock()
        mock_session_gen = Mock()
        mock_session_gen.__next__ = Mock(side_effect=[mock_session, StopIteration])
        mock_get_session.return_value = mock_session_gen
        
        # Setup mock source
        mock_source = Mock(spec=Source)
        mock_source.id = source_id
        mock_source.name = "Test Source"
        mock_source.type = "rss"
        mock_source.is_active = True
        
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_source
        
        # Setup mock RSS fetcher with error
        runner.rss_fetcher.fetch_articles.side_effect = Exception("Fetch failed")
        
        runner.run_single_source(source_id)
        
        mock_source.update_fetch_error.assert_called_once_with(mock_session, "Fetch failed", max_errors=10) 