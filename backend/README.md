# TLDR Backend

This is the backend service for the TLDR News Aggregator application.

## Features

- FastAPI-based REST API
- RSS feed aggregation
- Article content fetching
- PostgreSQL database integration
- Configurable content sources

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

### Setup

```bash
# Install dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Start the development server
uv run uvicorn app.main:app --reload
```

### CLI Commands

```bash
# Initialize database
uv run python -m app.fetcher.main --init-db

# Run health check
uv run python -m app.fetcher.main --health

# Fetch articles
uv run python -m app.fetcher.main --fetch
```

## API Documentation

When running the development server, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API Endpoints

All endpoints are prefixed with `/api/v1`. Standard HTTP status codes apply (200, 201, 400, 404, 500).

#### System
- `GET /health` - Health check with database status
- `GET /status` - Detailed system statistics (sources, articles, uptime)
- `POST /refresh` - Trigger manual refresh of all sources

#### Articles
- `GET /articles` - List articles with pagination
  - Query params: `days_back` (1-365, default: 7), `limit` (1-100, default: 20), `offset`, `source_id`, `sort` (newest/oldest)
  - Returns: `{articles: [...], total, limit, offset, has_more}`
- `GET /articles/{id}` - Get article details

#### Sources
- `GET /sources` - List sources with statistics
  - Query params: `include_inactive` (default: false)
- `POST /sources` - Create source
  - Body: `{url, name, type: "rss"|"website", is_active}`
- `GET /sources/{id}` - Get source details
- `PUT /sources/{id}` - Update source (partial updates supported)
- `DELETE /sources/{id}` - Delete source and all its articles 