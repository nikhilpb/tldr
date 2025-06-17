"""Article model for news articles fetched from sources."""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db.connection import Base


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