"""Main entry point for the Content Fetcher Service."""

import logging
import sys
import argparse
from typing import Optional
import json

from . import settings, create_database_tables, test_database_connection
from .rss_fetcher import RSSFetcher


def setup_logging(level: str = "INFO"):
    """Configure logging for the fetcher service."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def init_database():
    """Initialize database tables and test connection."""
    logger = logging.getLogger(__name__)
    
    logger.info("Testing database connection...")
    if not test_database_connection():
        logger.error("Database connection failed")
        return False
    
    logger.info("Creating database tables...")
    try:
        create_database_tables()
        logger.info("Database initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def health_check():
    """Perform health check of the fetcher service."""
    logger = logging.getLogger(__name__)
    
    # Test database connection
    if not test_database_connection():
        logger.error("Health check failed: Database connection error")
        return False
    
    # TODO: Add more health checks (source connectivity, disk space, etc.)
    
    logger.info("Health check passed")
    return True


def dry_run_rss(url: str, limit: int = 5):
    """
    Dry run RSS feed fetching - fetch and display articles without saving to database.
    
    Args:
        url: RSS feed URL to test
        limit: Number of articles to fetch and display (default: 5)
    """
    logger = logging.getLogger(__name__)
    
    logger.info(f"Dry run RSS fetch from: {url}")
    logger.info(f"Fetching up to {limit} articles...")
    
    try:
        fetcher = RSSFetcher()
        
        # Validate the RSS URL first
        if not fetcher.validate_rss_url(url):
            logger.error(f"Invalid RSS feed URL: {url}")
            return False
        
        # Fetch the feed
        feed = fetcher.fetch_feed(url)
        
        # Limit the number of entries to process
        entries_to_process = feed.entries[:limit] if len(feed.entries) > limit else feed.entries
        
        logger.info(f"Found {len(feed.entries)} total articles, showing first {len(entries_to_process)}")
        print("\n" + "="*80)
        print(f"RSS FEED DRY RUN RESULTS")
        print(f"URL: {url}")
        print(f"Feed Title: {getattr(feed.feed, 'title', 'Unknown')}")
        print(f"Feed Description: {getattr(feed.feed, 'description', 'No description')}")
        print("="*80)
        
        for i, entry in enumerate(entries_to_process, 1):
            try:
                article_data = fetcher.parse_entry(entry, url)
                
                print(f"\n[{i}] {article_data['title']}")
                print(f"    URL: {article_data['url']}")
                if article_data['author']:
                    print(f"    Author: {article_data['author']}")
                if article_data['published_at']:
                    print(f"    Published: {article_data['published_at'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
                if article_data['summary']:
                    # Truncate summary to avoid overwhelming output
                    summary = article_data['summary'][:200] + "..." if len(article_data['summary']) > 200 else article_data['summary']
                    print(f"    Summary: {summary}")
                print("-" * 40)
                
            except Exception as e:
                logger.error(f"Error parsing entry {i}: {e}")
                continue
        
        print(f"\nDry run completed successfully! Processed {len(entries_to_process)} articles.")
        return True
        
    except Exception as e:
        logger.error(f"Dry run failed: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Content Fetcher Service")
    parser.add_argument("--init-db", action="store_true", help="Initialize database tables")
    parser.add_argument("--health", action="store_true", help="Run health check")
    parser.add_argument("--dry-run-rss", type=str, metavar="URL", help="Dry run RSS feed fetching from URL")
    parser.add_argument("--limit", type=int, default=5, help="Number of articles to fetch in dry run (default: 5)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Set logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting Content Fetcher Service")
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"Concurrent limit: {settings.concurrent_limit}")
    
    success = True
    
    if args.init_db:
        success = init_database()
    
    if args.health:
        success = health_check()
    
    if args.dry_run_rss:
        success = dry_run_rss(args.dry_run_rss, args.limit)
    
    if not args.init_db and not args.health and not args.dry_run_rss:
        # Default action: show help
        parser.print_help()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()