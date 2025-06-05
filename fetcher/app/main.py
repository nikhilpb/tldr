"""Main entry point for the Content Fetcher Service."""

import logging
import sys
import argparse
from typing import Optional

from . import settings, create_database_tables, test_database_connection


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


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Content Fetcher Service")
    parser.add_argument("--init-db", action="store_true", help="Initialize database tables")
    parser.add_argument("--health", action="store_true", help="Run health check")
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
    
    if not args.init_db and not args.health:
        # Default action: show help
        parser.print_help()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()