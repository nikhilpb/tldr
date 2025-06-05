"""Database models for the Content Fetcher Service."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from typing import Optional

from .database import Base


class Source(Base):
    """
    Model for news sources (RSS feeds and websites).
    
    This model stores configuration and metadata for each news source
    that the fetcher will process.
    """
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(512), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # 'rss' or 'website'
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error tracking
    fetch_error_count = Column(Integer, default=0, nullable=False)
    last_error_message = Column(Text, nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship to articles
    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Source(id={self.id}, name='{self.name}', url='{self.url}', type='{self.type}')>"
    
    def is_healthy(self, max_errors: int = 10) -> bool:
        """Check if source is healthy (hasn't exceeded error threshold)."""
        return self.fetch_error_count < max_errors
    
    def update_fetch_success(self, session):
        """Update source after successful fetch."""
        self.last_fetched_at = datetime.now(timezone.utc)
        self.fetch_error_count = 0
        self.last_error_message = None
        self.last_error_at = None
        session.commit()
    
    def update_fetch_error(self, session, error_message: str, max_errors: int = 10):
        """Update source after fetch error."""
        self.fetch_error_count += 1
        self.last_error_message = error_message
        self.last_error_at = datetime.now(timezone.utc)
        
        # Auto-disable source if too many consecutive errors
        if self.fetch_error_count >= max_errors:
            self.is_active = False
        
        session.commit()


class Article(Base):
    """
    Model for news articles fetched from sources.
    
    This model stores the content and metadata for each article
    collected by the fetcher service.
    """
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    
    # Article metadata
    title = Column(String(512), nullable=False)
    url = Column(String(512), unique=True, nullable=False, index=True)
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Article content
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    
    # Fetcher metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship to source
    source = relationship("Source", back_populates="articles")
    
    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...', source_id={self.source_id})>"
    
    @classmethod
    def exists_by_url(cls, session, url: str) -> bool:
        """Check if article with given URL already exists."""
        return session.query(cls).filter(cls.url == url).first() is not None
    
    @classmethod
    def create_from_dict(cls, article_data: dict, source_id: int):
        """Create Article instance from dictionary data."""
        return cls(
            source_id=source_id,
            title=article_data.get("title", ""),
            url=article_data.get("url", ""),
            author=article_data.get("author"),
            published_at=article_data.get("published_at"),
            summary=article_data.get("summary"),
            content=article_data.get("content")
        )


class FetchLog(Base):
    """
    Model for tracking fetch operations and their results.
    
    This model stores metadata about each fetch operation for
    monitoring and debugging purposes.
    """
    __tablename__ = "fetch_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True, index=True)
    
    # Fetch operation metadata
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False)  # 'success', 'error', 'partial'
    
    # Results
    articles_found = Column(Integer, default=0, nullable=False)
    articles_new = Column(Integer, default=0, nullable=False)
    articles_updated = Column(Integer, default=0, nullable=False)
    
    # Error information
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)
    
    # Performance metrics
    duration_seconds = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<FetchLog(id={self.id}, source_id={self.source_id}, status='{self.status}')>"
    
    def mark_completed(self, status: str, articles_found: int = 0, articles_new: int = 0, 
                      error_message: Optional[str] = None, error_type: Optional[str] = None):
        """Mark fetch operation as completed with results."""
        self.completed_at = datetime.now(timezone.utc)
        self.status = status
        self.articles_found = articles_found
        self.articles_new = articles_new
        self.error_message = error_message
        self.error_type = error_type
        
        if self.started_at and self.completed_at:
            # Handle both timezone-aware and naive datetimes
            if self.started_at.tzinfo is None:
                started_at_utc = self.started_at.replace(tzinfo=timezone.utc)
            else:
                started_at_utc = self.started_at
            
            duration = self.completed_at - started_at_utc
            self.duration_seconds = int(duration.total_seconds())