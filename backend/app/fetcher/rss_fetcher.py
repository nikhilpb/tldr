"""RSS feed fetcher module for processing RSS feeds."""

import feedparser
import requests
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse
import logging
from email.utils import parsedate_to_datetime

from ..models import Source, Article

logger = logging.getLogger(__name__)


class RSSFetcher:
    """
    RSS feed fetcher that parses RSS feeds and extracts articles.
    
    This class handles the fetching and parsing of RSS feeds using feedparser,
    converting feed entries into article data that can be stored in the database.
    """
    
    def __init__(self, timeout: int = 30, user_agent: str = None):
        """
        Initialize RSS fetcher.
        
        Args:
            timeout: Request timeout in seconds
            user_agent: User agent string for requests
        """
        self.timeout = timeout
        self.user_agent = user_agent or "TLDR News Aggregator/1.0"
        
        # Configure feedparser
        feedparser.USER_AGENT = self.user_agent
    
    def fetch_feed(self, url: str) -> feedparser.FeedParserDict:
        """
        Fetch and parse RSS feed from URL.
        
        Args:
            url: RSS feed URL
            
        Returns:
            Parsed feed data
            
        Raises:
            requests.RequestException: If HTTP request fails
            Exception: If feed parsing fails
        """
        logger.info(f"Fetching RSS feed: {url}")
        
        try:
            # Use requests with custom headers and timeout
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'application/rss+xml, application/xml, text/xml',
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse the feed content
            feed = feedparser.parse(response.content)
            
            # Check for feed parsing errors
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"Feed parsing warning for {url}: {feed.bozo_exception}")
            
            if not hasattr(feed, 'entries') or len(feed.entries) == 0:
                raise Exception(f"No entries found in RSS feed: {url}")
            
            logger.info(f"Successfully parsed {len(feed.entries)} entries from {url}")
            return feed
            
        except requests.RequestException as e:
            logger.error(f"HTTP error fetching RSS feed {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing RSS feed {url}: {e}")
            raise
    
    def parse_entry(self, entry: Any, feed_url: str) -> Dict[str, Any]:
        """
        Parse a single RSS feed entry into article data.
        
        Args:
            entry: feedparser entry object
            feed_url: Original feed URL for resolving relative links
            
        Returns:
            Dictionary containing article data
        """
        # Extract title
        title = getattr(entry, 'title', '').strip()
        if not title:
            title = "Untitled"
        
        # Extract URL and ensure it's absolute
        url = getattr(entry, 'link', '').strip()
        if url and not urlparse(url).netloc:
            # Convert relative URL to absolute
            url = urljoin(feed_url, url)
        
        # Extract author
        author = None
        if hasattr(entry, 'author') and entry.author:
            author = entry.author.strip()
        elif hasattr(entry, 'authors') and entry.authors:
            try:
                author = entry.authors[0].get('name', '').strip()
            except (IndexError, AttributeError, TypeError):
                pass
        
        # Extract published date
        published_at = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                pass
        elif hasattr(entry, 'published'):
            try:
                published_at = parsedate_to_datetime(entry.published)
                # Ensure timezone awareness
                if published_at.tzinfo is None:
                    published_at = published_at.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                pass
        
        # Extract summary/description
        summary = None
        if hasattr(entry, 'summary'):
            summary = entry.summary.strip()
        elif hasattr(entry, 'description'):
            summary = entry.description.strip()
        
        # Extract content
        content = None
        if hasattr(entry, 'content') and entry.content:
            # feedparser content is a list of dictionaries
            content_items = []
            try:
                for content_item in entry.content:
                    if isinstance(content_item, dict) and content_item.get('value'):
                        content_items.append(content_item['value'])
                content = '\n'.join(content_items) if content_items else None
            except (TypeError, AttributeError):
                pass
        
        # If no content but we have summary, use summary as content
        if not content and summary:
            content = summary
        
        return {
            'title': title,
            'url': url,
            'author': author,
            'published_at': published_at,
            'summary': summary,
            'content': content
        }
    
    def fetch_articles(self, source: Source) -> List[Dict[str, Any]]:
        """
        Fetch and parse all articles from an RSS source.
        
        Args:
            source: Source model instance
            
        Returns:
            List of article data dictionaries
            
        Raises:
            Exception: If fetching or parsing fails
        """
        if source.type != 'rss':
            raise ValueError(f"Source {source.id} is not an RSS source (type: {source.type})")
        
        feed = self.fetch_feed(source.url)
        articles = []
        
        for entry in feed.entries:
            try:
                article_data = self.parse_entry(entry, source.url)
                
                # Skip entries without valid URL
                if not article_data.get('url'):
                    logger.warning(f"Skipping entry without URL from source {source.id}")
                    continue
                
                articles.append(article_data)
                
            except Exception as e:
                logger.error(f"Error parsing entry from source {source.id}: {e}")
                continue
        
        logger.info(f"Extracted {len(articles)} articles from RSS source {source.id}")
        return articles
    
    def validate_rss_url(self, url: str) -> bool:
        """
        Validate if URL is a valid RSS feed.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid RSS feed, False otherwise
        """
        try:
            feed = self.fetch_feed(url)
            return hasattr(feed, 'entries') and len(feed.entries) > 0
        except Exception:
            return False