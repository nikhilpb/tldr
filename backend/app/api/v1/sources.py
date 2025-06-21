"""Sources API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from ...db.session import get_database_session
from ...db.connection import create_database_engine
from ...core.config import settings
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

# Pydantic models for requests and responses
from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class SourceCreate(BaseModel):
    url: HttpUrl
    name: str
    type: str  # 'rss' or 'website'
    is_active: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://feeds.feedburner.com/example",
                "name": "Example News Feed",
                "type": "rss",
                "is_active": True
            }
        }

class SourceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated News Feed Name",
                "is_active": True
            }
        }

class SourceResponse(BaseModel):
    id: int
    url: str
    name: str
    type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_fetched_at: Optional[datetime] = None
    fetch_error_count: int
    last_error_message: Optional[str] = None
    last_error_at: Optional[datetime] = None
    article_count: Optional[int] = None
    
    class Config:
        from_attributes = True

class SourceListResponse(BaseModel):
    sources: List[SourceResponse]
    total: int

@router.get("/sources", response_model=SourceListResponse)
async def list_sources(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """
    List all sources with their statistics.
    
    Args:
        include_inactive: Whether to include inactive sources
    """
    try:
        query = db.query(Source)
        
        if not include_inactive:
            query = query.filter(Source.is_active == True)
        
        sources = query.order_by(desc(Source.created_at)).all()
        
        # Add article count for each source
        sources_response = []
        for source in sources:
            article_count = len(source.articles)  # Uses relationship
            
            sources_response.append(SourceResponse(
                id=source.id,
                url=source.url,
                name=source.name,
                type=source.type,
                is_active=source.is_active,
                created_at=source.created_at,
                updated_at=source.updated_at,
                last_fetched_at=source.last_fetched_at,
                fetch_error_count=source.fetch_error_count,
                last_error_message=source.last_error_message,
                last_error_at=source.last_error_at,
                article_count=article_count
            ))
        
        return SourceListResponse(
            sources=sources_response,
            total=len(sources)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sources: {str(e)}")

@router.post("/sources", response_model=SourceResponse, status_code=201)
async def create_source(
    source_data: SourceCreate,
    db: Session = Depends(get_db)
):
    """Create a new source."""
    try:
        # Validate source type
        if source_data.type not in ['rss', 'website']:
            raise HTTPException(status_code=400, detail="Source type must be 'rss' or 'website'")
        
        # Check if URL already exists
        existing_source = db.query(Source).filter(Source.url == str(source_data.url)).first()
        if existing_source:
            raise HTTPException(status_code=400, detail=f"Source with URL {source_data.url} already exists")
        
        # Create new source
        new_source = Source(
            url=str(source_data.url),
            name=source_data.name,
            type=source_data.type,
            is_active=source_data.is_active
        )
        
        db.add(new_source)
        db.commit()
        db.refresh(new_source)
        
        return SourceResponse(
            id=new_source.id,
            url=new_source.url,
            name=new_source.name,
            type=new_source.type,
            is_active=new_source.is_active,
            created_at=new_source.created_at,
            updated_at=new_source.updated_at,
            last_fetched_at=new_source.last_fetched_at,
            fetch_error_count=new_source.fetch_error_count,
            last_error_message=new_source.last_error_message,
            last_error_at=new_source.last_error_at,
            article_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create source: {str(e)}")

@router.get("/sources/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific source."""
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        
        if not source:
            raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
        
        article_count = len(source.articles)
        
        return SourceResponse(
            id=source.id,
            url=source.url,
            name=source.name,
            type=source.type,
            is_active=source.is_active,
            created_at=source.created_at,
            updated_at=source.updated_at,
            last_fetched_at=source.last_fetched_at,
            fetch_error_count=source.fetch_error_count,
            last_error_message=source.last_error_message,
            last_error_at=source.last_error_at,
            article_count=article_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get source: {str(e)}")

@router.put("/sources/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int,
    source_data: SourceUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing source."""
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        
        if not source:
            raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
        
        # Update fields that were provided
        if source_data.name is not None:
            source.name = source_data.name
        
        if source_data.type is not None:
            if source_data.type not in ['rss', 'website']:
                raise HTTPException(status_code=400, detail="Source type must be 'rss' or 'website'")
            source.type = source_data.type
        
        if source_data.is_active is not None:
            source.is_active = source_data.is_active
        
        db.commit()
        db.refresh(source)
        
        article_count = len(source.articles)
        
        return SourceResponse(
            id=source.id,
            url=source.url,
            name=source.name,
            type=source.type,
            is_active=source.is_active,
            created_at=source.created_at,
            updated_at=source.updated_at,
            last_fetched_at=source.last_fetched_at,
            fetch_error_count=source.fetch_error_count,
            last_error_message=source.last_error_message,
            last_error_at=source.last_error_at,
            article_count=article_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update source: {str(e)}")

@router.delete("/sources/{source_id}")
async def delete_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a source and all its associated articles.
    
    Warning: This operation is irreversible and will delete all articles from this source.
    """
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        
        if not source:
            raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
        
        # Get article count before deletion
        article_count = len(source.articles)
        source_name = source.name
        
        # Delete source (cascade will delete articles)
        db.delete(source)
        db.commit()
        
        return {
            "message": f"Source '{source_name}' (ID: {source_id}) deleted successfully",
            "deleted_articles": article_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete source: {str(e)}") 