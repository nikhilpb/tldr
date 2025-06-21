"""System API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import Dict, Any
from datetime import datetime, timezone

from ...db.session import get_database_session
from ...db.connection import create_database_engine, test_database_connection
from ...core.config import settings
from ...models.source import Source
from ...models.article import Article
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

# Pydantic models
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str
    version: str
    uptime_seconds: Optional[float] = None

class SystemStatsResponse(BaseModel):
    status: str
    timestamp: datetime
    database: Dict[str, Any]
    sources: Dict[str, Any]
    articles: Dict[str, Any]
    system: Dict[str, Any]

# Store application start time for uptime calculation
app_start_time = datetime.now(timezone.utc)

@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    
    Returns system health status including database connectivity.
    """
    try:
        # Test database connection
        db_status = "healthy"
        try:
            db.execute(text("SELECT 1"))
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        # Calculate uptime
        uptime = (datetime.now(timezone.utc) - app_start_time).total_seconds()
        
        return HealthResponse(
            status="healthy" if db_status == "healthy" else "degraded",
            timestamp=datetime.now(timezone.utc),
            database=db_status,
            version="1.0.0",
            uptime_seconds=uptime
        )
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@router.get("/status", response_model=SystemStatsResponse)
async def system_status(db: Session = Depends(get_db)):
    """
    Detailed system status and statistics.
    
    Returns comprehensive information about the system state,
    including database statistics, source counts, and article metrics.
    """
    try:
        current_time = datetime.now(timezone.utc)
        
        # Database statistics
        db_stats = {
            "status": "healthy",
            "connection_test": True
        }
        
        try:
            db.execute(text("SELECT 1"))
        except Exception as e:
            db_stats["status"] = "unhealthy"
            db_stats["connection_test"] = False
            db_stats["error"] = str(e)
        
        # Source statistics
        total_sources = db.query(Source).count()
        active_sources = db.query(Source).filter(Source.is_active == True).count()
        sources_with_errors = db.query(Source).filter(Source.fetch_error_count > 0).count()
        
        # Recent source activity
        recently_fetched = db.query(Source).filter(
            Source.last_fetched_at.isnot(None)
        ).count()
        
        sources_stats = {
            "total": total_sources,
            "active": active_sources,
            "inactive": total_sources - active_sources,
            "with_errors": sources_with_errors,
            "recently_fetched": recently_fetched
        }
        
        # Article statistics
        total_articles = db.query(Article).count()
        
        # Articles from last 24 hours
        yesterday = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        recent_articles = db.query(Article).filter(
            Article.created_at >= yesterday
        ).count()
        
        # Get oldest and newest article dates
        oldest_article = db.query(func.min(Article.created_at)).scalar()
        newest_article = db.query(func.max(Article.created_at)).scalar()
        
        articles_stats = {
            "total": total_articles,
            "added_today": recent_articles,
            "oldest_article": oldest_article.isoformat() if oldest_article else None,
            "newest_article": newest_article.isoformat() if newest_article else None
        }
        
        # System information
        uptime = (current_time - app_start_time).total_seconds()
        
        system_info = {
            "uptime_seconds": uptime,
            "start_time": app_start_time.isoformat(),
            "database_url_type": "sqlite" if settings.database_url.startswith("sqlite") else "postgresql",
            "fetch_interval_hours": settings.fetch_interval_hours,
            "article_retention_days": settings.article_retention_days
        }
        
        return SystemStatsResponse(
            status="healthy" if db_stats["status"] == "healthy" else "degraded",
            timestamp=current_time,
            database=db_stats,
            sources=sources_stats,
            articles=articles_stats,
            system=system_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

@router.post("/refresh")
async def trigger_refresh():
    """
    Trigger a manual refresh of all sources.
    
    Note: This endpoint is a placeholder for manual refresh functionality.
    In production, this might trigger a background task or queue job.
    """
    try:
        # TODO: Implement manual refresh trigger
        # This could:
        # 1. Queue a background task to run the fetcher
        # 2. Send a signal to the fetcher service
        # 3. Return job ID for status tracking
        
        return {
            "message": "Manual refresh triggered",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "queued",
            "note": "Manual refresh functionality is not yet implemented. Use the CLI fetcher for now."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger refresh: {str(e)}") 