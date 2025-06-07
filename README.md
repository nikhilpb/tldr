# News Aggregator

A web application that aggregates news from various sources including RSS feeds and blog-like websites.

## Quick Start

1. **Clone and setup environment:**
   ```bash
   git clone <repository-url>
   cd tldr
   cp .env.example .env
   ```

2. **Start with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Development

### Local Development Setup

1. **Backend setup:**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Frontend setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Fetcher service (now part of backend):**
   ```bash
   cd backend
   python -m app.fetcher.main --help
   ```

### Project Structure

```
├── backend/           # FastAPI backend service with integrated fetcher
│   ├── app/
│   │   ├── api/       # API endpoints
│   │   ├── core/      # Configuration and utilities
│   │   ├── db/        # Database models and connections
│   │   ├── fetcher/   # Content fetching service
│   │   │   ├── config.py    # Fetcher configuration
│   │   │   ├── database.py  # Database connection
│   │   │   ├── main.py      # CLI entry point
│   │   │   └── models.py    # Shared database models
│   │   └── models/    # Pydantic models
│   └── tests/
│       └── fetcher/   # Fetcher tests
├── frontend/          # React TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── types/
│   └── public/
├── docker/            # Docker configuration files
├── database/          # Database schemas and migrations
└── docker-compose.yml # Multi-service orchestration
```

## Features (V1)

- **Single User Support**: Local configuration and preferences
- **Source Management**: Add/remove RSS feeds and website sources (up to 100)
- **Content Aggregation**: Hourly refresh from all active sources
- **Article Storage**: 1-year retention period with full-text search
- **Web Interface**: Clean, responsive design for article browsing
- **Search & Filter**: Find articles by content, source, or date

## Technology Stack

- **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React 18, TypeScript, Material-UI, React Query
- **Content Fetching**: feedparser, BeautifulSoup4, requests
- **Deployment**: Docker, Docker Compose
- **Database**: PostgreSQL (production), SQLite (development)

## API Endpoints

```
Sources Management:
GET    /api/v1/sources              # List all sources
POST   /api/v1/sources              # Add new source
PUT    /api/v1/sources/{id}         # Update source
DELETE /api/v1/sources/{id}         # Delete source

Articles:
GET    /api/v1/articles             # List articles with pagination
GET    /api/v1/articles/search      # Search articles
GET    /api/v1/articles/{id}        # Get article details

System:
POST   /api/v1/refresh              # Trigger manual refresh
GET    /api/v1/health               # Health check
```

## Environment Variables

See `.env.example` for all configuration options.

## Contributing

1. Follow the development phases outlined in `DESIGN.md`
2. Run tests before submitting changes
3. Follow the established code style and patterns