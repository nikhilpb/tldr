"""Feed discovery module for detecting RSS and Atom feeds on webpages."""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)


class FeedDiscovery:
    """
    Feed discovery utility for detecting RSS and Atom feeds on webpages.
    
    This class can parse HTML pages and find feed links in the document head,
    returning information about available RSS and Atom feeds.
    """
    
    def __init__(self, timeout: int = 10, user_agent: str = None):
        """
        Initialize feed discovery.
        
        Args:
            timeout: Request timeout in seconds
            user_agent: User agent string for requests
        """
        self.timeout = timeout
        self.user_agent = user_agent or "TLDR Feed Discovery/1.0"
    
    def discover_feeds(self, url: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Discover RSS and Atom feeds on a webpage.
        
        Args:
            url: URL of the webpage to analyze
            
        Returns:
            Dictionary with 'rss' and 'atom' keys containing lists of found feeds
            Each feed is a dict with 'url', 'title', and 'type' keys
            
        Raises:
            requests.RequestException: If HTTP request fails
            Exception: If HTML parsing fails
        """
        logger.info(f"Discovering feeds on: {url}")
        
        try:
            # Fetch the webpage
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find feed links
            feeds = self._parse_feed_links(soup, url)
            
            logger.info(f"Found {len(feeds['rss'])} RSS feeds and {len(feeds['atom'])} Atom feeds on {url}")
            return feeds
            
        except requests.RequestException as e:
            logger.error(f"HTTP error fetching webpage {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing webpage {url}: {e}")
            raise
    
    def _parse_feed_links(self, soup: BeautifulSoup, base_url: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Parse HTML soup to find RSS and Atom feed links.
        
        Args:
            soup: BeautifulSoup parsed HTML
            base_url: Base URL for resolving relative links
            
        Returns:
            Dictionary with 'rss' and 'atom' keys containing feed information
        """
        feeds = {'rss': [], 'atom': []}
        
        # Look for link elements with rel="alternate" in the head
        head = soup.find('head')
        if not head:
            return feeds
        
        # Find all link elements with rel="alternate"
        feed_links = head.find_all('link', rel='alternate')
        
        for link in feed_links:
            feed_type = link.get('type', '').lower()
            feed_url = link.get('href', '').strip()
            feed_title = link.get('title', '').strip()
            
            if not feed_url:
                continue
            
            # Convert relative URLs to absolute
            if not urlparse(feed_url).netloc:
                feed_url = urljoin(base_url, feed_url)
            
            # Classify feed type
            if 'rss' in feed_type or 'rss+xml' in feed_type:
                feeds['rss'].append({
                    'url': feed_url,
                    'title': feed_title or 'RSS Feed',
                    'type': feed_type
                })
            elif 'atom' in feed_type or 'atom+xml' in feed_type:
                feeds['atom'].append({
                    'url': feed_url,
                    'title': feed_title or 'Atom Feed',
                    'type': feed_type
                })
        
        return feeds
    
    def has_feeds(self, url: str) -> Dict[str, bool]:
        """
        Simple check to see if a webpage has RSS and/or Atom feeds.
        
        Args:
            url: URL of the webpage to check
            
        Returns:
            Dictionary with 'has_rss' and 'has_atom' boolean keys
        """
        try:
            feeds = self.discover_feeds(url)
            return {
                'has_rss': len(feeds['rss']) > 0,
                'has_atom': len(feeds['atom']) > 0
            }
        except Exception as e:
            logger.error(f"Error checking feeds for {url}: {e}")
            return {'has_rss': False, 'has_atom': False}


def discover_feeds_simple(url: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Simple function to discover feeds on a webpage.
    
    Args:
        url: URL of the webpage to analyze
        
    Returns:
        Dictionary with 'rss' and 'atom' keys containing feed information
    """
    discovery = FeedDiscovery()
    return discovery.discover_feeds(url)


def has_feeds_simple(url: str) -> Dict[str, bool]:
    """
    Simple function to check if a webpage has feeds.
    
    Args:
        url: URL of the webpage to check
        
    Returns:
        Dictionary with 'has_rss' and 'has_atom' boolean keys
    """
    discovery = FeedDiscovery()
    return discovery.has_feeds(url)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python feed_discovery.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    
    try:
        discovery = FeedDiscovery()
        feeds = discovery.discover_feeds(url)
        
        print(f"\nFeed Discovery Results for: {url}")
        print("=" * 50)
        
        if feeds['rss']:
            print(f"\nRSS Feeds ({len(feeds['rss'])}):")
            for i, feed in enumerate(feeds['rss'], 1):
                print(f"  {i}. {feed['title']}")
                print(f"     URL: {feed['url']}")
                print(f"     Type: {feed['type']}")
        else:
            print("\nNo RSS feeds found.")
        
        if feeds['atom']:
            print(f"\nAtom Feeds ({len(feeds['atom'])}):")
            for i, feed in enumerate(feeds['atom'], 1):
                print(f"  {i}. {feed['title']}")
                print(f"     URL: {feed['url']}")
                print(f"     Type: {feed['type']}")
        else:
            print("\nNo Atom feeds found.")
        
        # Summary
        has_feeds = discovery.has_feeds(url)
        print(f"\nSummary:")
        print(f"  Has RSS feeds: {has_feeds['has_rss']}")
        print(f"  Has Atom feeds: {has_feeds['has_atom']}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 