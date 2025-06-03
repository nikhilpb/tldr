# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **News Aggregator App** project currently in the planning phase. The application will collect and display news articles from various sources including RSS feeds and blog-like websites. Version 1 targets a single user with up to 100 configurable news sources, hourly refresh rates, and 1-year article retention.

## Current Project Status

**Planning Phase**: The repository contains comprehensive planning documentation but no implementation code yet. Key documents:
- `PRD.md`: Product Requirements Document with feature specifications
- `DESIGN.md`: Engineering design document with detailed technical architecture

## Planned Technology Stack

Based on the design documentation:

### Backend (Recommended: Python + FastAPI)
- **Framework**: FastAPI for REST API service
- **Content Fetching**: BeautifulSoup4 + requests for web scraping, feedparser for RSS
- **Database**: PostgreSQL for production, SQLite for local development
- **ORM**: SQLAlchemy + Alembic for migrations
- **Task Scheduling**: APScheduler or Celery for hourly content refresh
- **Testing**: pytest

### Frontend (Recommended: React + TypeScript)
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Library**: Material-UI or Tailwind CSS
- **State Management**: React Query for server state
- **Routing**: React Router

### Deployment
- **Development**: Docker Compose for local multi-service setup
- **Production**: GCP Compute Engine with Docker containers (recommended) or Cloud Run
- **Database**: Cloud SQL (PostgreSQL) for production
- **Alternative Options**: Node.js backend or Go for better performance
- **Monitoring**: GCP Cloud Logging and Monitoring

## System Architecture

The application follows a microservices-inspired architecture:
```
Frontend (Web App) ↔ Backend API Service ↔ Content Fetcher Service
                            ↓                        ↓
                     Database Layer         Scheduler Service
```

### Key Components:
1. **Frontend**: Source management and article browsing interface
2. **Backend API**: RESTful endpoints for data management
3. **Content Fetcher**: RSS parsing and web scraping service
4. **Scheduler**: Hourly content refresh and cleanup (1-year retention)
5. **Database**: Article and source storage with full-text search

## Development Workflow (When Implementation Begins)

### Local Setup:
```bash
# Development environment
docker-compose up

# Database migrations (when implemented)
alembic upgrade head

# Run tests (when implemented)
pytest

# Linting (when implemented)
flake8 .
black .
```

### Key Requirements:
- Support up to 100 news sources per user
- Hourly content refresh from all active sources
- 1-year article retention period
- No content filtering/moderation in v1
- Web-only platform for v1

## API Design (Planned)

RESTful endpoints to be implemented:
```
Sources: GET/POST/PUT/DELETE /api/sources
Articles: GET /api/articles, GET /api/articles/search
System: POST /api/refresh, GET /api/health
```

## Data Models (Planned)

### Sources Table
- URL, name, type (RSS/website), active status
- Fetch tracking and error counts

### Articles Table  
- Source reference, title, URL, author, published date
- Summary, content, full-text search vectors
- Performance indexes on published_at, source_id, search

## Development Phases (Planned)

1. **Phase 1**: Docker development environment setup
2. **Phase 2**: FastAPI backend with basic CRUD operations
3. **Phase 3**: Content fetcher service (RSS + web scraping)
4. **Phase 4**: React frontend application
5. **Phase 5**: GCP deployment
6. **Phase 6**: Monitoring and CI/CD pipeline (TBD)

## Simplified Scope for V1

Recent design updates emphasize:
- **Caching**: Out of scope for v1
- **Scaling**: Out of scope for v1  
- **CI/CD Pipeline**: To be determined
- **Monitoring**: To be determined

## When Starting Implementation

Since this is a planning-phase project, when beginning implementation:
1. Create appropriate directory structure (`backend/`, `frontend/`, `fetcher/`, `docker/`)
2. Initialize package management files (`requirements.txt`, `package.json`)
3. Set up Docker Compose for local development with multi-stage Dockerfiles
4. Follow the technology recommendations and data models in `DESIGN.md`
5. Implement the phased approach, focusing on core functionality first
6. Use the provided SQL schemas for PostgreSQL with full-text search capabilities