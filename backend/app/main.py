from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import sources, articles, system
from app.core.config import settings

app = FastAPI(
    title="News Aggregator API",
    description="API for aggregating news from various sources",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources.router, prefix="/api/v1", tags=["sources"])
app.include_router(articles.router, prefix="/api/v1", tags=["articles"])
app.include_router(system.router, prefix="/api/v1", tags=["system"])

@app.get("/")
async def root():
    return {"message": "News Aggregator API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}