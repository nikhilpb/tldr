"""Shared database models package for the News Aggregator application."""

# Import and re-export models from dedicated modules
from .source import Source
from .article import Article

# Export all models for easy importing
__all__ = ["Source", "Article"] 