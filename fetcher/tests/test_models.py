"""Tests for database models."""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Source, Article, FetchLog


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


class TestSourceModel:
    """Tests for the Source model."""
    
    def test_create_source(self, test_db_session):
        """Test creating a new source."""
        source = Source(
            url="https://example.com/rss.xml",
            name="Example RSS Feed",
            type="rss"
        )
        
        test_db_session.add(source)
        test_db_session.commit()
        
        assert source.id is not None
        assert source.url == "https://example.com/rss.xml"
        assert source.name == "Example RSS Feed"
        assert source.type == "rss"
        assert source.is_active is True
        assert source.fetch_error_count == 0
        assert source.created_at is not None
    
    def test_source_is_healthy(self, test_db_session):
        """Test source health check."""
        source = Source(
            url="https://example.com/rss.xml",
            name="Example RSS Feed",
            type="rss",
            fetch_error_count=5
        )
        
        assert source.is_healthy(max_errors=10) is True
        
        source.fetch_error_count = 15
        assert source.is_healthy(max_errors=10) is False
    
    def test_update_fetch_success(self, test_db_session):
        """Test updating source after successful fetch."""
        source = Source(
            url="https://example.com/rss.xml",
            name="Example RSS Feed",
            type="rss",
            fetch_error_count=3,
            last_error_message="Previous error"
        )
        
        test_db_session.add(source)
        test_db_session.commit()
        
        source.update_fetch_success(test_db_session)
        
        assert source.fetch_error_count == 0
        assert source.last_error_message is None
        assert source.last_error_at is None
        assert source.last_fetched_at is not None
    
    def test_update_fetch_error(self, test_db_session):
        """Test updating source after fetch error."""
        source = Source(
            url="https://example.com/rss.xml",
            name="Example RSS Feed",
            type="rss"
        )
        
        test_db_session.add(source)
        test_db_session.commit()
        
        source.update_fetch_error(test_db_session, "Connection timeout", max_errors=3)
        
        assert source.fetch_error_count == 1
        assert source.last_error_message == "Connection timeout"
        assert source.last_error_at is not None
        assert source.is_active is True  # Still below threshold
        
        # Simulate multiple errors to trigger auto-disable
        source.fetch_error_count = 2
        source.update_fetch_error(test_db_session, "Another error", max_errors=3)
        
        assert source.fetch_error_count == 3
        assert source.is_active is False  # Should be auto-disabled


class TestArticleModel:
    """Tests for the Article model."""
    
    def test_create_article(self, test_db_session):
        """Test creating a new article."""
        # First create a source
        source = Source(
            url="https://example.com/rss.xml",
            name="Example RSS Feed",
            type="rss"
        )
        test_db_session.add(source)
        test_db_session.commit()
        
        # Create article
        article = Article(
            source_id=source.id,
            title="Test Article",
            url="https://example.com/article1",
            author="Test Author",
            summary="This is a test article summary",
            content="This is the full content of the test article"
        )
        
        test_db_session.add(article)
        test_db_session.commit()
        
        assert article.id is not None
        assert article.source_id == source.id
        assert article.title == "Test Article"
        assert article.url == "https://example.com/article1"
        assert article.author == "Test Author"
        assert article.created_at is not None
    
    def test_article_exists_by_url(self, test_db_session):
        """Test checking if article exists by URL."""
        # First create a source
        source = Source(
            url="https://example.com/rss.xml",
            name="Example RSS Feed",
            type="rss"
        )
        test_db_session.add(source)
        test_db_session.commit()
        
        # Test non-existent article
        assert Article.exists_by_url(test_db_session, "https://example.com/nonexistent") is False
        
        # Create article
        article = Article(
            source_id=source.id,
            title="Test Article",
            url="https://example.com/article1"
        )
        test_db_session.add(article)
        test_db_session.commit()
        
        # Test existing article
        assert Article.exists_by_url(test_db_session, "https://example.com/article1") is True
    
    def test_create_from_dict(self, test_db_session):
        """Test creating article from dictionary data."""
        article_data = {
            "title": "Dict Article",
            "url": "https://example.com/dict-article",
            "author": "Dict Author",
            "summary": "Dict summary",
            "content": "Dict content",
            "published_at": datetime.now(timezone.utc)
        }
        
        article = Article.create_from_dict(article_data, source_id=1)
        
        assert article.title == "Dict Article"
        assert article.url == "https://example.com/dict-article"
        assert article.author == "Dict Author"
        assert article.summary == "Dict summary"
        assert article.content == "Dict content"
        assert article.source_id == 1


class TestFetchLogModel:
    """Tests for the FetchLog model."""
    
    def test_create_fetch_log(self, test_db_session):
        """Test creating a new fetch log."""
        # First create a source
        source = Source(
            url="https://example.com/rss.xml",
            name="Example RSS Feed",
            type="rss"
        )
        test_db_session.add(source)
        test_db_session.commit()
        
        # Create fetch log
        fetch_log = FetchLog(
            source_id=source.id,
            status="success"
        )
        
        test_db_session.add(fetch_log)
        test_db_session.commit()
        
        assert fetch_log.id is not None
        assert fetch_log.source_id == source.id
        assert fetch_log.status == "success"
        assert fetch_log.started_at is not None
        assert fetch_log.articles_found == 0
        assert fetch_log.articles_new == 0
    
    def test_mark_completed(self, test_db_session):
        """Test marking fetch log as completed."""
        fetch_log = FetchLog(
            source_id=1,
            status="running"
        )
        
        test_db_session.add(fetch_log)
        test_db_session.commit()
        
        fetch_log.mark_completed(
            status="success",
            articles_found=10,
            articles_new=3
        )
        
        assert fetch_log.status == "success"
        assert fetch_log.articles_found == 10
        assert fetch_log.articles_new == 3
        assert fetch_log.completed_at is not None
        assert fetch_log.duration_seconds is not None