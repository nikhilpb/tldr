"""Main entry point for the Content Fetcher Service."""

import logging
import sys
import argparse
from typing import Optional
import json
import os

from . import settings, create_database_tables, test_database_connection, get_database_session
from ..models import Source, Article
from .rss_fetcher import RSSFetcher
from .runner import FetcherRunner


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


def run_fetcher():
    """Run the main fetch cycle across all active sources."""
    logger = logging.getLogger(__name__)
    
    try:
        runner = FetcherRunner()
        runner.run_fetch_cycle()
        return True
    except Exception as e:
        logger.error(f"Fetch cycle failed: {e}")
        return False


def run_single_source(source_id: int):
    """Run fetch for a single source."""
    logger = logging.getLogger(__name__)
    
    try:
        runner = FetcherRunner()
        runner.run_single_source(source_id)
        return True
    except Exception as e:
        logger.error(f"Single source fetch failed: {e}")
        return False


def list_sources():
    """List all sources in the database."""
    logger = logging.getLogger(__name__)
    
    try:
        db_session = next(get_database_session())
        sources = db_session.query(Source).all()
        
        if not sources:
            print("No sources found in database.")
            return True
        
        print("\n" + "="*80)
        print(f"SOURCES LIST ({len(sources)} total)")
        print("="*80)
        
        for source in sources:
            status = "🟢 Active" if source.is_active else "🔴 Inactive"
            error_info = f" ({source.fetch_error_count} errors)" if source.fetch_error_count > 0 else ""
            
            print(f"\n[{source.id}] {source.name}")
            print(f"    URL: {source.url}")
            print(f"    Type: {source.type.upper()}")
            print(f"    Status: {status}{error_info}")
            
            if source.last_fetched_at:
                print(f"    Last Fetched: {source.last_fetched_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            else:
                print(f"    Last Fetched: Never")
            
            if source.last_error_message:
                error_msg = source.last_error_message[:100] + "..." if len(source.last_error_message) > 100 else source.last_error_message
                print(f"    Last Error: {error_msg}")
            
            print("-" * 40)
        
        print(f"\nTotal: {len(sources)} sources")
        active_count = sum(1 for s in sources if s.is_active)
        print(f"Active: {active_count}, Inactive: {len(sources) - active_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to list sources: {e}")
        return False


def add_sources_from_json(file_path: str):
    """Add sources from JSON file to database."""
    logger = logging.getLogger(__name__)
    
    try:
        if not os.path.exists(file_path):
            logger.error(f"JSON file not found: {file_path}")
            return False
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'sources' not in data:
            logger.error("JSON file must contain 'sources' array")
            return False
        
        sources_data = data['sources']
        if not isinstance(sources_data, list):
            logger.error("'sources' must be an array")
            return False
        
        if not sources_data:
            logger.info("No sources found in JSON file")
            return True
        
        db_session = next(get_database_session())
        added_count = 0
        skipped_count = 0
        
        print(f"\nProcessing {len(sources_data)} sources from {file_path}...")
        
        for i, source_data in enumerate(sources_data, 1):
            try:
                # Validate required fields
                required_fields = ['name', 'url', 'type']
                for field in required_fields:
                    if field not in source_data:
                        logger.error(f"Source {i}: Missing required field '{field}'")
                        continue
                
                # Check if source already exists
                existing = db_session.query(Source).filter(Source.url == source_data['url']).first()
                if existing:
                    print(f"[{i}] Skipped: {source_data['name']} (URL already exists)")
                    skipped_count += 1
                    continue
                
                # Create new source
                new_source = Source(
                    name=source_data['name'],
                    url=source_data['url'],
                    type=source_data['type'],
                    is_active=source_data.get('is_active', True)
                )
                
                db_session.add(new_source)
                db_session.commit()
                
                print(f"[{i}] Added: {source_data['name']} ({source_data['type']})")
                added_count += 1
                
            except Exception as e:
                logger.error(f"Error processing source {i}: {e}")
                db_session.rollback()
                continue
        
        print(f"\nSummary:")
        print(f"  Added: {added_count} sources")
        print(f"  Skipped: {skipped_count} sources (already exist)")
        print(f"  Total processed: {len(sources_data)} sources")
        
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to add sources from JSON: {e}")
        return False


def list_recent_articles(source_id: int, limit: int = 10):
    """List recent articles from a specific source."""
    logger = logging.getLogger(__name__)
    
    try:
        db_session = next(get_database_session())
        
        # First, check if source exists
        source = db_session.query(Source).filter(Source.id == source_id).first()
        if not source:
            print(f"❌ Source with ID {source_id} not found.")
            return False
        
        # Query articles from this source, ordered by most recent first
        articles = db_session.query(Article).filter(
            Article.source_id == source_id
        ).order_by(
            Article.published_at.desc().nullslast(),  # Published date first (nulls last)
            Article.created_at.desc()  # Then creation date
        ).limit(limit).all()
        
        if not articles:
            print(f"📭 No articles found for source '{source.name}' (ID: {source_id}).")
            return True
        
        print("\n" + "="*80)
        print(f"RECENT ARTICLES FROM SOURCE: {source.name}")
        print(f"Source ID: {source_id} | Type: {source.type.upper()}")
        print(f"Showing {len(articles)} most recent articles (limit: {limit})")
        print("="*80)
        
        for i, article in enumerate(articles, 1):
            print(f"\n[{i}] {article.title}")
            print(f"    URL: {article.url}")
            
            if article.author:
                print(f"    Author: {article.author}")
            
            if article.published_at:
                print(f"    Published: {article.published_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            print(f"    Added to DB: {article.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            if article.summary:
                # Truncate summary to avoid overwhelming output
                summary = article.summary[:300] + "..." if len(article.summary) > 300 else article.summary
                print(f"    Summary: {summary}")
            
            print("-" * 40)
        
        print(f"\nTotal articles shown: {len(articles)}")
        if len(articles) == limit:
            total_count = db_session.query(Article).filter(Article.source_id == source_id).count()
            if total_count > limit:
                print(f"Note: This source has {total_count} total articles. Use --limit to see more.")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to list articles for source {source_id}: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Content Fetcher Service")
    parser.add_argument("--init-db", action="store_true", help="Initialize database tables")
    parser.add_argument("--health", action="store_true", help="Run health check")
    parser.add_argument("--dry-run-rss", type=str, metavar="URL", help="Dry run RSS feed fetching from URL")
    parser.add_argument("--fetch", action="store_true", help="Run fetch cycle across all active sources")
    parser.add_argument("--fetch-source", type=int, metavar="ID", help="Fetch articles from a single source by ID")
    parser.add_argument("--list-sources", action="store_true", help="List all sources in database")
    parser.add_argument("--list-articles", type=int, metavar="SOURCE_ID", help="List recent articles from a specific source")
    parser.add_argument("--add-sources", type=str, metavar="FILE", help="Add sources from JSON file")
    parser.add_argument("--limit", type=int, help="Number of articles to fetch in dry run or list (default: 5 for dry-run, 10 for list-articles)")
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
        limit = args.limit if args.limit is not None else 5
        success = dry_run_rss(args.dry_run_rss, limit)
    
    if args.fetch:
        success = run_fetcher()
    
    if args.fetch_source:
        success = run_single_source(args.fetch_source)
    
    if args.list_sources:
        success = list_sources()
    
    if args.list_articles:
        limit = args.limit if args.limit is not None else 10
        success = list_recent_articles(args.list_articles, limit)
    
    if args.add_sources:
        success = add_sources_from_json(args.add_sources)
    
    if not any([args.init_db, args.health, args.dry_run_rss, args.fetch, args.fetch_source, args.list_sources, args.list_articles, args.add_sources]):
        # Default action: show help
        parser.print_help()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()