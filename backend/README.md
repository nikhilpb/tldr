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