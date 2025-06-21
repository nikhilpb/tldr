"""Articles API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from ...db.session import get_database_session
from ...db.connection import create_database_engine
from ...core.config import settings
from ...models.article import Article
from ...models.source import Source
from sqlalchemy.orm import sessionmaker

# Create database session
engine = create_database_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session dependency."""
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

router = APIRouter()

# Pydantic models for responses
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ArticleResponse(BaseModel):
    id: int
    title: str
    url: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    created_at: datetime
    source_id: int
    source_name: str
    
    class Config:
        from_attributes = True

class ArticleListResponse(BaseModel):
    articles: List[ArticleResponse]
    total: int
    limit: int
    offset: int
    has_more: bool

class ArticleDetailResponse(BaseModel):
    id: int
    title: str
    url: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    created_at: datetime
    source_id: int
    source_name: str
    source_url: str
    
    class Config:
        from_attributes = True

@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    days_back: Optional[int] = Query(7, ge=1, le=365, description="Number of days back to fetch articles"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="Number of articles per page"),
    offset: Optional[int] = Query(0, ge=0, description="Pagination offset"),
    source_id: Optional[int] = Query(None, description="Filter by source ID"),
    sort: Optional[str] = Query("newest", regex="^(newest|oldest)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    """
    List articles with pagination and date filtering.
    
    Supports filtering by:
    - Date range (days_back from today)
    - Source ID 
    - Pagination with limit/offset
    - Sort order (newest/oldest)
    """
    try:
        # Calculate date cutoff
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        # Build query
        query = db.query(Article).join(Source)
        
        # Apply date filter - use published_at if available, otherwise created_at
        query = query.filter(
            (Article.published_at >= cutoff_date) | 
            ((Article.published_at.is_(None)) & (Article.created_at >= cutoff_date))
        )
        
        # Apply source filter if specified
        if source_id:
            # Verify source exists
            source_exists = db.query(Source).filter(Source.id == source_id).first()
            if not source_exists:
                raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
            query = query.filter(Article.source_id == source_id)
        
        # Apply sorting
        if sort == "newest":
            query = query.order_by(
                desc(Article.published_at).nullslast(),
                desc(Article.created_at)
            )
        else:  # oldest
            query = query.order_by(
                Article.published_at.asc().nullsfirst(),
                Article.created_at.asc()
            )
        
        # Get total count before applying pagination
        total = query.count()
        
        # Apply pagination
        articles_query = query.offset(offset).limit(limit).all()
        
        # Transform to response format
        articles_response = []
        for article in articles_query:
            articles_response.append(ArticleResponse(
                id=article.id,
                title=article.title,
                url=article.url,
                author=article.author,
                published_at=article.published_at,
                summary=article.summary,
                content=article.content,
                created_at=article.created_at,
                source_id=article.source_id,
                source_name=article.source.name
            ))
        
        return ArticleListResponse(
            articles=articles_response,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/articles/{article_id}", response_model=ArticleDetailResponse)
async def get_article(
    article_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific article."""
    try:
        article = db.query(Article).join(Source).filter(Article.id == article_id).first()
        
        if not article:
            raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
        
        return ArticleDetailResponse(
            id=article.id,
            title=article.title,
            url=article.url,
            author=article.author,
            published_at=article.published_at,
            summary=article.summary,
            content=article.content,
            created_at=article.created_at,
            source_id=article.source_id,
            source_name=article.source.name,
            source_url=article.source.url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get article: {str(e)}") 