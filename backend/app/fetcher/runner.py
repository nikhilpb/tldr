"""FetcherRunner class for running the article fetching process across all sources."""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from .database import get_database_session
from .models import Source, Article
from .rss_fetcher import RSSFetcher
from .config import settings

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
                    
                    # Update source success status
                    self.update_source_fetch_status(session, source, success=True)
                    
                    # TODO: Implement deduplication logic
                    # - Check if articles already exist in database by URL
                    # - Compare article content for duplicates across sources
                    # - Handle updated articles (same URL, different content)
                    
                    # TODO: Write articles to articles table
                    # - Create Article objects from article dictionaries
                    # - Batch insert for performance
                    # - Handle database constraints (unique URLs, etc.)
                    # - Update article metadata (created_at, source_id, etc.)
                    
                    logger.debug(f"TODO: Need to dedupe and save {len(articles)} articles from source {source.id}")
                    
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
                self.update_source_fetch_status(session, source, success=True)
                
                # TODO: Same deduplication and storage logic as run_fetch_cycle
                logger.debug(f"TODO: Need to dedupe and save {len(articles)} articles from source {source_id}")
                
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