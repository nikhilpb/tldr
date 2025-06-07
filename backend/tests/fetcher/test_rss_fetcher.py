"""Unit tests for RSS fetcher module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import feedparser
import requests

from app.fetcher.rss_fetcher import RSSFetcher
from app.fetcher.models import Source


class TestRSSFetcher:
    """Test suite for RSSFetcher class."""
    
    @pytest.fixture
    def rss_fetcher(self):
        """Create RSSFetcher instance for testing."""
        return RSSFetcher(timeout=10, user_agent="Test Agent/1.0")
    
    @pytest.fixture
    def mock_source(self):
        """Create mock RSS source for testing."""
        source = Mock(spec=Source)
        source.id = 1
        source.url = "https://example.com/feed.rss"
        source.type = "rss"
        source.name = "Test RSS Feed"
        return source
    
    @pytest.fixture
    def sample_feed_data(self):
        """Sample feed data for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <description>A test RSS feed</description>
                <link>https://example.com</link>
                <item>
                    <title>Test Article 1</title>
                    <link>https://example.com/article1</link>
                    <description>This is a test article</description>
                    <author>John Doe</author>
                    <pubDate>Wed, 01 Jan 2020 12:00:00 GMT</pubDate>
                </item>
                <item>
                    <title>Test Article 2</title>
                    <link>https://example.com/article2</link>
                    <description>Another test article</description>
                    <pubDate>Thu, 02 Jan 2020 12:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>"""
    
    def test_init(self):
        """Test RSSFetcher initialization."""
        fetcher = RSSFetcher(timeout=20, user_agent="Custom Agent")
        assert fetcher.timeout == 20
        assert fetcher.user_agent == "Custom Agent"
        assert feedparser.USER_AGENT == "Custom Agent"
    
    def test_init_default_values(self):
        """Test RSSFetcher initialization with default values."""
        fetcher = RSSFetcher()
        assert fetcher.timeout == 30
        assert fetcher.user_agent == "TLDR News Aggregator/1.0"
    
    @patch('app.fetcher.rss_fetcher.requests.get')
    def test_fetch_feed_success(self, mock_get, rss_fetcher, sample_feed_data):
        """Test successful RSS feed fetching."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.content = sample_feed_data.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        url = "https://example.com/feed.rss"
        feed = rss_fetcher.fetch_feed(url)
        
        # Verify request was made correctly
        mock_get.assert_called_once_with(
            url,
            headers={
                'User-Agent': "Test Agent/1.0",
                'Accept': 'application/rss+xml, application/xml, text/xml',
            },
            timeout=10
        )
        
        # Verify feed parsing
        assert hasattr(feed, 'entries')
        assert len(feed.entries) == 2
        assert feed.entries[0].title == "Test Article 1"
        assert feed.entries[1].title == "Test Article 2"
    
    @patch('app.fetcher.rss_fetcher.requests.get')
    def test_fetch_feed_http_error(self, mock_get, rss_fetcher):
        """Test RSS feed fetching with HTTP error."""
        mock_get.side_effect = requests.RequestException("Connection failed")
        
        url = "https://example.com/feed.rss"
        with pytest.raises(requests.RequestException, match="Connection failed"):
            rss_fetcher.fetch_feed(url)
    
    @patch('app.fetcher.rss_fetcher.requests.get')
    def test_fetch_feed_empty_feed(self, mock_get, rss_fetcher):
        """Test RSS feed fetching with empty feed."""
        empty_feed = """<?xml version="1.0"?><rss><channel></channel></rss>"""
        mock_response = Mock()
        mock_response.content = empty_feed.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        url = "https://example.com/feed.rss"
        with pytest.raises(Exception, match="No entries found in RSS feed"):
            rss_fetcher.fetch_feed(url)
    
    def test_parse_entry_complete_data(self, rss_fetcher):
        """Test parsing RSS entry with complete data."""
        # Create mock entry with all fields
        entry = Mock()
        entry.title = "Test Article"
        entry.link = "https://example.com/article"
        entry.author = "John Doe"
        entry.published_parsed = (2020, 1, 1, 12, 0, 0, 2, 1, 0)
        entry.summary = "Article summary"
        entry.content = [{"value": "Article content"}]
        
        feed_url = "https://example.com/feed.rss"
        result = rss_fetcher.parse_entry(entry, feed_url)
        
        assert result['title'] == "Test Article"
        assert result['url'] == "https://example.com/article"
        assert result['author'] == "John Doe"
        assert result['published_at'] == datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert result['summary'] == "Article summary"
        assert result['content'] == "Article content"
    
    def test_parse_entry_minimal_data(self, rss_fetcher):
        """Test parsing RSS entry with minimal data."""
        class MinimalEntry:
            title = "Minimal Article"
            link = "https://example.com/minimal"
        
        entry = MinimalEntry()
        feed_url = "https://example.com/feed.rss"
        result = rss_fetcher.parse_entry(entry, feed_url)
        
        assert result['title'] == "Minimal Article"
        assert result['url'] == "https://example.com/minimal"
        assert result['author'] is None
        assert result['published_at'] is None
        assert result['summary'] is None
        assert result['content'] is None
    
    def test_parse_entry_relative_url(self, rss_fetcher):
        """Test parsing RSS entry with relative URL."""
        class RelativeEntry:
            title = "Relative URL Article"
            link = "/relative-article"
        
        entry = RelativeEntry()
        feed_url = "https://example.com/feed.rss"
        result = rss_fetcher.parse_entry(entry, feed_url)
        
        assert result['url'] == "https://example.com/relative-article"
    
    def test_parse_entry_empty_title(self, rss_fetcher):
        """Test parsing RSS entry with empty title."""
        class EmptyTitleEntry:
            title = ""
            link = "https://example.com/notitle"
        
        entry = EmptyTitleEntry()
        feed_url = "https://example.com/feed.rss"
        result = rss_fetcher.parse_entry(entry, feed_url)
        
        assert result['title'] == "Untitled"
    
    def test_parse_entry_multiple_content_items(self, rss_fetcher):
        """Test parsing RSS entry with multiple content items."""
        class MultiContentEntry:
            title = "Multi Content Article"
            link = "https://example.com/multi"
            content = [
                {"value": "Content part 1"},
                {"value": "Content part 2"},
                {"value": ""}  # Empty content should be included
            ]
        
        entry = MultiContentEntry()
        feed_url = "https://example.com/feed.rss"
        result = rss_fetcher.parse_entry(entry, feed_url)
        
        assert result['content'] == "Content part 1\nContent part 2"
    
    def test_parse_entry_authors_list(self, rss_fetcher):
        """Test parsing RSS entry with authors list."""
        class AuthorsEntry:
            title = "Multi Author Article"
            link = "https://example.com/authors"
            authors = [{"name": "Jane Doe"}, {"name": "John Smith"}]
        
        entry = AuthorsEntry()
        feed_url = "https://example.com/feed.rss"
        result = rss_fetcher.parse_entry(entry, feed_url)
        
        assert result['author'] == "Jane Doe"  # Should use first author
    
    @patch.object(RSSFetcher, 'fetch_feed')
    def test_fetch_articles_success(self, mock_fetch_feed, rss_fetcher, mock_source):
        """Test successful article fetching from RSS source."""
        # Mock feed data
        mock_feed = Mock()
        mock_entry1 = Mock()
        mock_entry1.title = "Article 1"
        mock_entry1.link = "https://example.com/article1"
        mock_entry2 = Mock()
        mock_entry2.title = "Article 2"
        mock_entry2.link = "https://example.com/article2"
        mock_feed.entries = [mock_entry1, mock_entry2]
        mock_fetch_feed.return_value = mock_feed
        
        with patch.object(rss_fetcher, 'parse_entry') as mock_parse:
            mock_parse.side_effect = [
                {"title": "Article 1", "url": "https://example.com/article1"},
                {"title": "Article 2", "url": "https://example.com/article2"}
            ]
            
            articles = rss_fetcher.fetch_articles(mock_source)
            
            assert len(articles) == 2
            assert articles[0]["title"] == "Article 1"
            assert articles[1]["title"] == "Article 2"
            mock_fetch_feed.assert_called_once_with(mock_source.url)
    
    def test_fetch_articles_wrong_source_type(self, rss_fetcher, mock_source):
        """Test fetch_articles with non-RSS source type."""
        mock_source.type = "website"
        
        with pytest.raises(ValueError, match="Source 1 is not an RSS source"):
            rss_fetcher.fetch_articles(mock_source)
    
    @patch.object(RSSFetcher, 'fetch_feed')
    def test_fetch_articles_skip_invalid_entries(self, mock_fetch_feed, rss_fetcher, mock_source):
        """Test fetch_articles skips entries without valid URLs."""
        mock_feed = Mock()
        mock_entry1 = Mock()
        mock_entry1.title = "Valid Article"
        mock_entry1.link = "https://example.com/valid"
        mock_entry2 = Mock()
        mock_entry2.title = "Invalid Article"
        mock_entry2.link = ""  # Invalid URL
        mock_feed.entries = [mock_entry1, mock_entry2]
        mock_fetch_feed.return_value = mock_feed
        
        with patch.object(rss_fetcher, 'parse_entry') as mock_parse:
            mock_parse.side_effect = [
                {"title": "Valid Article", "url": "https://example.com/valid"},
                {"title": "Invalid Article", "url": ""}  # Empty URL
            ]
            
            articles = rss_fetcher.fetch_articles(mock_source)
            
            assert len(articles) == 1
            assert articles[0]["title"] == "Valid Article"
    
    @patch.object(RSSFetcher, 'fetch_feed')
    def test_validate_rss_url_valid(self, mock_fetch_feed, rss_fetcher):
        """Test RSS URL validation with valid feed."""
        mock_feed = Mock()
        mock_feed.entries = [Mock()]  # At least one entry
        mock_fetch_feed.return_value = mock_feed
        
        result = rss_fetcher.validate_rss_url("https://example.com/valid.rss")
        assert result is True
    
    @patch.object(RSSFetcher, 'fetch_feed')
    def test_validate_rss_url_invalid(self, mock_fetch_feed, rss_fetcher):
        """Test RSS URL validation with invalid feed."""
        mock_fetch_feed.side_effect = Exception("Invalid feed")
        
        result = rss_fetcher.validate_rss_url("https://example.com/invalid.rss")
        assert result is False
    
    @patch.object(RSSFetcher, 'fetch_feed')
    def test_validate_rss_url_empty_feed(self, mock_fetch_feed, rss_fetcher):
        """Test RSS URL validation with empty feed."""
        mock_feed = Mock()
        mock_feed.entries = []  # No entries
        mock_fetch_feed.return_value = mock_feed
        
        result = rss_fetcher.validate_rss_url("https://example.com/empty.rss")
        assert result is False