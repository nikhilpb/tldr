"""Source model for news sources (RSS feeds and websites)."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone

from ..db.connection import Base


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