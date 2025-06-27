# News Aggregator

A web application that aggregates news from various sources including RSS feeds and blog-like websites.

## Quick Start

TODO

## Setup

### Prerequisites

Install [uv](https://docs.astral.sh/uv/) for Python dependency management:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using Homebrew
brew install uv

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Backend Setup

```bash
cd backend

# Install dependencies with dev tools (creates virtual environment automatically)
uv sync --extra dev

# Initialize database tables (if needed)
uv run python -m app.fetcher.main --init-db
```

## Development

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

### Running Tests

* Backend: `cd backend && uv run pytest tests/ -v`
* Test Coverage: `cd backend && uv run pytest tests/ --cov=app --cov-report=html --cov-report=term-missing`

### Content Fetcher CLI

The fetcher service includes a CLI for database management and RSS feed testing:

```bash
cd backend

# Initialize database tables
uv run python -m app.fetcher.main --init-db

# Run health check
uv run python -m app.fetcher.main --health

# Test RSS feed (dry run - no database save)
uv run python -m app.fetcher.main --dry-run-rss https://feeds.bbci.co.uk/news/rss.xml --limit 5

# Run fetch cycle across all active sources
uv run python -m app.fetcher.main --fetch

# Fetch from a single source by ID
uv run python -m app.fetcher.main --fetch-source 1

# List all sources in database
uv run python -m app.fetcher.main --list-sources

# Add sources from JSON file
uv run python -m app.fetcher.main --add-sources app/fetcher/sources.json

# Set logging level
uv run python -m app.fetcher.main --health --log-level DEBUG
```

**CLI Options:**
- `--init-db` - Initialize database tables
- `--health` - Run health check
- `--dry-run-rss URL` - Test RSS feed without saving to database
- `--fetch` - Run fetch cycle across all active sources
- `--fetch-source ID` - Fetch articles from a single source by ID
- `--list-sources` - List all sources in database with status and metadata
- `--add-sources FILE` - Add sources from JSON file to database
- `--limit N` - Number of articles to show in dry run (default: 5)
- `--log-level LEVEL` - Set logging level (DEBUG, INFO, WARNING, ERROR)

**JSON Source Format:**
```json
{
  "sources": [
    {
      "name": "OpenAI News",
      "url": "https://openai.com/news/rss.xml",
      "type": "rss",
      "is_active": true
    }
  ]
}
```

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
GET    /api/v1/health               # Health check
```