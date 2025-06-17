"""FetcherRunner class for running the article fetching process across all sources."""

import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
import hashlib
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from ..db import get_database_session as _get_database_session, create_database_engine
from ..models import Source, Article
from .rss_fetcher import RSSFetcher
from .config import settings
from sqlalchemy.orm import sessionmaker

# Create database session for this module
engine = create_database_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_database_session():
    """Get database session for runner."""
    yield from _get_database_session(SessionLocal)

logger = logging.getLogger(__name__)


class FetcherRunner:
    """
    Main runner class that orchestrates fetching articles from all sources.
    
    This class queries all active sources from the database and fetches articles
    from each source using the appropriate fetcher (RSS, website, etc.).
    """
    
    def __init__(self):
        """Initialize the FetcherRunner with fetcher instances."""
        self.rss_fetcher = RSSFetcher(
            timeout=settings.request_timeout // 1000,  # Convert ms to seconds
            user_agent=settings.user_agent
        )
        
        # Configuration for article processing
        self.batch_size = 100  # Process articles in batches
        self.max_title_length = 512
        self.max_content_length = 50000  # 50KB limit for content
        self.max_summary_length = 5000   # 5KB limit for summary
    
    def get_active_sources(self, session: Session) -> List[Source]:
        """
        Query all active sources from the database.
        
        Args:
            session: Database session
            
        Returns:
            List of active Source objects
        """
        try:
            sources = session.query(Source).filter(
                Source.is_active == True
            ).all()
            
            logger.info(f"Found {len(sources)} active sources in database")
            return sources
            
        except Exception as e:
            logger.error(f"Error querying active sources: {e}")
            raise
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize URL by removing tracking parameters and ensuring consistent format.
        
        Args:
            url: Original URL
            
        Returns:
            Normalized URL
        """
        if not url:
            return url
        
        try:
            parsed = urlparse(url)
            
            # Remove common tracking parameters
            tracking_params = {
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
                'fbclid', 'gclid', 'ref', 'referrer', '_ga', 'mc_cid', 'mc_eid'
            }
            
            query_params = parse_qs(parsed.query)
            filtered_params = {k: v for k, v in query_params.items() 
                             if k.lower() not in tracking_params}
            
            # Rebuild query string
            new_query = urlencode(filtered_params, doseq=True) if filtered_params else ''
            
            # Rebuild URL
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc.lower(),  # Normalize domain to lowercase
                parsed.path,
                parsed.params,
                new_query,
                ''  # Remove fragment
            ))
            
            return normalized
            
        except Exception as e:
            logger.warning(f"Error normalizing URL '{url}': {e}")
            return url
    
    def validate_article_data(self, article_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate article data before storage.
        
        Args:
            article_data: Article data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields
        if not article_data.get('title', '').strip():
            return False, "Article title is required"
        
        if not article_data.get('url', '').strip():
            return False, "Article URL is required"
        
        # Validate URL format
        url = article_data['url']
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, f"Invalid URL format: {url}"
        except Exception:
            return False, f"Invalid URL format: {url}"
        
        # Check field lengths
        title = article_data.get('title', '')
        if len(title) > self.max_title_length:
            return False, f"Title too long ({len(title)} > {self.max_title_length})"
        
        content = article_data.get('content', '') or ''
        if len(content) > self.max_content_length:
            return False, f"Content too long ({len(content)} > {self.max_content_length})"
        
        summary = article_data.get('summary', '') or ''
        if len(summary) > self.max_summary_length:
            return False, f"Summary too long ({len(summary)} > {self.max_summary_length})"
        
        return True, None
    
    def generate_content_hash(self, article_data: Dict[str, Any]) -> str:
        """
        Generate content hash for duplicate detection.
        
        Args:
            article_data: Article data dictionary
            
        Returns:
            SHA256 hash of normalized content
        """
        # Combine title and content for hashing
        title = article_data.get('title', '').strip().lower()
        content = article_data.get('content', '') or article_data.get('summary', '') or ''
        content = content.strip().lower()
        
        # Create hash from combined content
        combined = f"{title}|{content}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    def check_duplicate_by_url(self, session: Session, url: str) -> Optional[Article]:
        """
        Check if article exists by URL.
        
        Args:
            session: Database session
            url: Article URL to check
            
        Returns:
            Existing Article object if found, None otherwise
        """
        try:
            return session.query(Article).filter(Article.url == url).first()
        except Exception as e:
            logger.error(f"Error checking duplicate by URL '{url}': {e}")
            return None
    
    def check_duplicate_by_content(self, session: Session, content_hash: str, 
                                 source_id: int) -> Optional[Article]:
        """
        Check if similar article exists by content hash.
        Note: This is a simplified implementation. In production, you might want
        to store content hashes in a separate table for better performance.
        
        Args:
            session: Database session
            content_hash: Content hash to check
            source_id: Source ID to exclude from search (allow same content from same source)
            
        Returns:
            Existing Article object if found, None otherwise
        """
        # For v1, we'll skip content-based deduplication to keep it simple
        # This can be implemented later with a dedicated content_hashes table
        return None
    
    def prepare_article_for_storage(self, article_data: Dict[str, Any], 
                                  source_id: int) -> Dict[str, Any]:
        """
        Prepare article data for database storage.
        
        Args:
            article_data: Raw article data
            source_id: ID of source
            
        Returns:
            Prepared article data ready for storage
        """
        # Normalize URL
        normalized_url = self.normalize_url(article_data.get('url', ''))
        
        # Truncate fields if necessary
        title = article_data.get('title', '').strip()
        if len(title) > self.max_title_length:
            title = title[:self.max_title_length-3] + '...'
        
        content = article_data.get('content', '') or ''
        if len(content) > self.max_content_length:
            content = content[:self.max_content_length-3] + '...'
        
        summary = article_data.get('summary', '') or ''
        if len(summary) > self.max_summary_length:
            summary = summary[:self.max_summary_length-3] + '...'
        
        return {
            'source_id': source_id,
            'title': title,
            'url': normalized_url,
            'author': article_data.get('author'),
            'published_at': article_data.get('published_at'),
            'summary': summary if summary else None,
            'content': content if content else None
        }
    
    def store_articles_batch(self, session: Session, articles_data: List[Dict[str, Any]], 
                           source_id: int) -> Tuple[int, int, int]:
        """
        Store a batch of articles to database with deduplication.
        
        Args:
            session: Database session
            articles_data: List of article data dictionaries
            source_id: Source ID
            
        Returns:
            Tuple of (stored_count, duplicate_count, error_count)
        """
        stored_count = 0
        duplicate_count = 0
        error_count = 0
        
        logger.info(f"Processing batch of {len(articles_data)} articles from source {source_id}")
        
        for i, article_data in enumerate(articles_data):
            try:
                # Validate article data
                is_valid, error_msg = self.validate_article_data(article_data)
                if not is_valid:
                    logger.warning(f"Invalid article data from source {source_id}: {error_msg}")
                    error_count += 1
                    continue
                
                # Prepare article for storage
                prepared_data = self.prepare_article_for_storage(article_data, source_id)
                normalized_url = prepared_data['url']
                
                # Check for duplicate by URL
                existing_article = self.check_duplicate_by_url(session, normalized_url)
                if existing_article:
                    logger.debug(f"Duplicate article found (URL): {normalized_url}")
                    duplicate_count += 1
                    continue
                
                # Create new article
                new_article = Article.create_from_dict(prepared_data, source_id)
                session.add(new_article)
                
                # Commit individual article to handle potential constraint violations
                try:
                    session.commit()
                    stored_count += 1
                    logger.debug(f"Stored article: {prepared_data['title'][:50]}...")
                    
                except IntegrityError as e:
                    # Handle race condition where article was inserted by another process
                    session.rollback()
                    if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e).lower():
                        logger.debug(f"Duplicate article detected during insert: {normalized_url}")
                        duplicate_count += 1
                    else:
                        logger.error(f"Database integrity error for article '{prepared_data['title']}': {e}")
                        error_count += 1
                
            except Exception as e:
                logger.error(f"Error processing article {i+1} from source {source_id}: {e}")
                error_count += 1
                try:
                    session.rollback()
                except:
                    pass
                continue
        
        logger.info(f"Batch processing completed: {stored_count} stored, {duplicate_count} duplicates, {error_count} errors")
        return stored_count, duplicate_count, error_count
    
    def process_articles_from_source(self, session: Session, articles: List[Dict[str, Any]], 
                                   source_id: int) -> Dict[str, int]:
        """
        Process and store all articles from a source.
        
        Args:
            session: Database session
            articles: List of article data dictionaries
            source_id: Source ID
            
        Returns:
            Dictionary with processing statistics
        """
        if not articles:
            return {'stored': 0, 'duplicates': 0, 'errors': 0}
        
        logger.info(f"Processing {len(articles)} articles from source {source_id}")
        
        total_stored = 0
        total_duplicates = 0
        total_errors = 0
        
        # Process articles in batches
        for i in range(0, len(articles), self.batch_size):
            batch = articles[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(articles) + self.batch_size - 1) // self.batch_size
            
            logger.debug(f"Processing batch {batch_num}/{total_batches} ({len(batch)} articles)")
            
            stored, duplicates, errors = self.store_articles_batch(session, batch, source_id)
            
            total_stored += stored
            total_duplicates += duplicates
            total_errors += errors
        
        stats = {
            'stored': total_stored,
            'duplicates': total_duplicates,
            'errors': total_errors
        }
        
        logger.info(f"Source {source_id} processing completed: {stats}")
        return stats
    
    def fetch_articles_from_source(self, source: Source) -> List[Dict[str, Any]]:
        """
        Fetch articles from a single source using the appropriate fetcher.
        
        Args:
            source: Source object to fetch from
            
        Returns:
            List of article dictionaries
            
        Raises:
            ValueError: If source type is not supported
            Exception: If fetching fails
        """
        logger.info(f"Fetching articles from source: {source.name} ({source.type})")
        
        if source.type == 'rss':
            return self.rss_fetcher.fetch_articles(source)
        elif source.type == 'website':
            # TODO: Implement website scraper
            logger.warning(f"Website fetching not yet implemented for source {source.id}")
            return []
        else:
            raise ValueError(f"Unsupported source type: {source.type}")
    
    def log_fetch_results(self, source: Source, articles: List[Dict[str, Any]], 
                         error: Optional[Exception] = None):
        """
        Log the results of fetching from a source.
        
        Args:
            source: Source that was fetched from
            articles: List of articles fetched (empty if error occurred)
            error: Exception if fetching failed
        """
        if error:
            logger.error(f"Failed to fetch from source '{source.name}' (ID: {source.id}): {error}")
        else:
            logger.info(f"Successfully fetched {len(articles)} articles from source '{source.name}' (ID: {source.id})")
            
            # Log some sample article data for debugging
            if articles and logger.isEnabledFor(logging.DEBUG):
                for i, article in enumerate(articles[:3]):  # Log first 3 articles
                    logger.debug(f"  Article {i+1}: {article.get('title', 'No title')[:50]}...")
    
    def update_source_fetch_status(self, session: Session, source: Source, 
                                 success: bool, error_message: Optional[str] = None):
        """
        Update source fetch status in database.
        
        Args:
            session: Database session
            source: Source to update
            success: Whether fetch was successful
            error_message: Error message if fetch failed
        """
        try:
            if success:
                source.update_fetch_success(session)
                logger.debug(f"Updated fetch success for source {source.id}")
            else:
                source.update_fetch_error(
                    session, 
                    error_message or "Unknown error",
                    max_errors=settings.max_consecutive_errors
                )
                logger.debug(f"Updated fetch error for source {source.id}")
                
        except Exception as e:
            logger.error(f"Error updating source {source.id} fetch status: {e}")
    
    def run_fetch_cycle(self):
        """
        Run a complete fetch cycle across all active sources.
        
        This method:
        1. Queries all active sources from the database
        2. Fetches articles from each source
        3. Logs the responses
        4. Updates source fetch status
        5. Leaves TODO for deduplication and article storage
        """
        logger.info("Starting fetch cycle")
        
        total_articles_fetched = 0
        total_articles_stored = 0
        total_duplicates = 0
        total_errors = 0
        sources_processed = 0
        sources_failed = 0
        
        # Get database session
        session_gen = get_database_session()
        session = next(session_gen)
        
        try:
            # Get all active sources
            sources = self.get_active_sources(session)
            
            if not sources:
                logger.warning("No active sources found in database")
                return
            
            # Process each source
            for source in sources:
                sources_processed += 1
                articles = []
                error = None
                
                try:
                    # Fetch articles from source
                    articles = self.fetch_articles_from_source(source)
                    total_articles_fetched += len(articles)
                    
                    # Log results
                    self.log_fetch_results(source, articles)
                    
                    # Process and store articles
                    storage_stats = self.process_articles_from_source(session, articles, source.id)
                    
                    # Update totals
                    total_articles_stored += storage_stats['stored']
                    total_duplicates += storage_stats['duplicates'] 
                    total_errors += storage_stats['errors']
                    
                    # Update source success status
                    self.update_source_fetch_status(session, source, success=True)
                    
                    # Log storage results
                    logger.info(f"Source {source.id} storage completed: "
                               f"{storage_stats['stored']} stored, "
                               f"{storage_stats['duplicates']} duplicates, "
                               f"{storage_stats['errors']} errors")
                    
                except Exception as e:
                    error = e
                    sources_failed += 1
                    
                    # Log error
                    self.log_fetch_results(source, [], error=error)
                    
                    # Update source error status
                    self.update_source_fetch_status(session, source, success=False, 
                                                  error_message=str(error))
        
            # Log summary
            logger.info(f"Fetch cycle completed:")
            logger.info(f"  Sources processed: {sources_processed}")
            logger.info(f"  Sources failed: {sources_failed}")
            logger.info(f"  Total articles fetched: {total_articles_fetched}")
            logger.info(f"  Total articles stored: {total_articles_stored}")
            logger.info(f"  Total duplicates skipped: {total_duplicates}")
            logger.info(f"  Total errors: {total_errors}")
            
        except Exception as e:
            logger.error(f"Fatal error during fetch cycle: {e}")
            raise
            
        finally:
            # Close database session
            try:
                next(session_gen, None)
            except StopIteration:
                pass
    
    def run_single_source(self, source_id: int):
        """
        Run fetch for a single source by ID.
        
        Args:
            source_id: ID of source to fetch from
        """
        logger.info(f"Running fetch for single source ID: {source_id}")
        
        # Get database session
        session_gen = get_database_session()
        session = next(session_gen)
        
        try:
            # Get the specific source
            source = session.query(Source).filter(Source.id == source_id).first()
            
            if not source:
                logger.error(f"Source with ID {source_id} not found")
                return
            
            if not source.is_active:
                logger.warning(f"Source {source_id} is not active")
                return
            
            # Fetch articles
            try:
                articles = self.fetch_articles_from_source(source)
                self.log_fetch_results(source, articles)
                
                # Process and store articles
                storage_stats = self.process_articles_from_source(session, articles, source_id)
                
                self.update_source_fetch_status(session, source, success=True)
                
                # Log storage results
                logger.info(f"Single source {source_id} storage completed: "
                           f"{storage_stats['stored']} stored, "
                           f"{storage_stats['duplicates']} duplicates, "
                           f"{storage_stats['errors']} errors")
                
            except Exception as e:
                self.log_fetch_results(source, [], error=e)
                self.update_source_fetch_status(session, source, success=False, 
                                              error_message=str(e))
                
        finally:
            # Close database session
            try:
                next(session_gen, None)
            except StopIteration:
                pass 