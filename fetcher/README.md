# Content Fetcher Service

## Overview

The Content Fetcher Service is responsible for collecting articles from configured news sources, including RSS feeds and blog-style websites. It operates as a scheduled service that periodically fetches content from all active sources and stores normalized article data in the database.

## Architecture Integration

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Scheduler     │───►│   Content       │───►│   Backend API   │
│   Service       │    │   Fetcher       │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         └──────────────►│   RSS Feeds     │              │
                        │   Websites      │◄─────────────┘
                        └─────────────────┘
```

## Fetching Workflow

### 1. Scheduled Execution
- **Frequency**: Hourly execution triggered by the Scheduler Service
- **Trigger**: HTTP endpoint `/fetch` or internal scheduler call
- **Parallelization**: Concurrent fetching from multiple sources with configurable limits

### 2. Source Processing Pipeline

```
Active Sources Query → Source Type Detection → Content Fetching → Content Parsing → Article Extraction → Database Storage
```

#### Step-by-Step Process:
1. **Source Discovery**: Query database for all `sources` where `is_active = true`
2. **Type Detection**: Determine if source is RSS/Atom feed or website
3. **Content Fetching**: HTTP request with appropriate headers and user agent
4. **Content Parsing**: 
   - RSS/Atom: Use feedparser library
   - Website: Use BeautifulSoup for content extraction
5. **Article Extraction**: Extract title, URL, author, published date, summary, content
6. **Deduplication**: Check if article URL already exists in database
7. **Database Storage**: Insert new articles with source reference

### 3. Error Handling & Resilience

#### Retry Logic
- **Initial Retry**: 3 attempts with exponential backoff (1s, 2s, 4s)
- **Timeout Handling**: 30-second timeout per source request
- **Failed Source Tracking**: Increment `fetch_error_count` in sources table
- **Source Deactivation**: Auto-disable sources after 10 consecutive failures

#### Error Categories
- **Network Errors**: DNS resolution, connection timeouts, HTTP errors
- **Parsing Errors**: Invalid RSS/XML, malformed HTML
- **Content Errors**: Missing required fields, encoding issues

### 4. Rate Limiting & Respectful Crawling

#### Implementation Strategy
- **Request Delay**: Minimum 1-second delay between requests to same domain
- **Concurrent Limits**: Maximum 5 concurrent requests across all sources
- **User Agent**: Identify as news aggregator with contact information
- **Robots.txt**: Respect robots.txt directives for website sources
- **Cache Headers**: Honor cache-control and etag headers when possible

## Source Types

### RSS/Atom Feeds
```python
# Example RSS processing
import feedparser

def fetch_rss_source(source_url):
    feed = feedparser.parse(source_url)
    for entry in feed.entries:
        article = {
            'title': entry.title,
            'url': entry.link,
            'author': getattr(entry, 'author', None),
            'published_at': parse_datetime(entry.published),
            'summary': entry.summary,
            'content': extract_content(entry)
        }
        yield article
```

### Website Sources
```python
# Example website scraping
from bs4 import BeautifulSoup

def fetch_website_source(source_url):
    # Extract article links from main page
    article_links = extract_article_links(source_url)
    
    for article_url in article_links:
        article_html = fetch_page(article_url)
        soup = BeautifulSoup(article_html, 'html.parser')
        
        article = {
            'title': extract_title(soup),
            'url': article_url,
            'author': extract_author(soup),
            'published_at': extract_date(soup),
            'content': extract_main_content(soup)
        }
        yield article
```

## Data Flow

### Input
- **Source Configuration**: From `sources` table in database
- **Fetch Parameters**: Last fetch timestamp, error counts, active status

### Processing
- **Content Retrieval**: HTTP requests to source URLs
- **Content Parsing**: RSS/HTML parsing and article extraction
- **Data Normalization**: Standardize article format across source types

### Output
- **Article Records**: Inserted into `articles` table
- **Source Updates**: Update `last_fetched_at` and `fetch_error_count`
- **Fetch Logs**: Structured logging for monitoring and debugging

## Configuration

### Environment Variables
```bash
FETCHER_CONCURRENT_LIMIT=5        # Max concurrent requests
FETCHER_REQUEST_DELAY=1000        # Delay between requests (ms)
FETCHER_REQUEST_TIMEOUT=30000     # Request timeout (ms)
FETCHER_MAX_RETRIES=3             # Retry attempts
FETCHER_USER_AGENT="NewsAgg/1.0"  # HTTP User-Agent string
```

### Database Integration
- **Connection**: Shared database connection with Backend API
- **Transactions**: Atomic operations for article insertion
- **Indexing**: Efficient queries using source_id and published_at indexes

## Monitoring & Health Checks

### Metrics to Track
- **Success Rate**: Percentage of successful fetches per source
- **Processing Time**: Average time to process each source
- **Article Volume**: Number of new articles fetched per hour
- **Error Frequency**: Types and frequency of fetch errors

### Health Check Endpoint
```http
GET /health
Response: {
  "status": "healthy",
  "last_run": "2024-01-15T10:00:00Z",
  "sources_processed": 45,
  "articles_fetched": 123,
  "errors": 2
}
```

## Development Setup

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run single fetch cycle
python -m app.main --fetch

# Run with specific source
python -m app.main --source-id 1

# Run health check
python -m app.main --health
```

### Docker Development
```bash
# Build fetcher image
docker build -f ../docker/Dockerfile.fetcher -t news-fetcher .

# Run fetcher service
docker run -e DATABASE_URL=postgresql://... news-fetcher
```

## Implementation Status

### Phase 1: Core Infrastructure
- [x] **Set up database models, configuration, and connection management** ✅
  - ✅ Database models: `Source`, `Article`, `FetchLog` with full relationships
  - ✅ Configuration management with Pydantic settings and environment variables
  - ✅ Database connection handling for SQLite (dev) and PostgreSQL (prod)
  - ✅ Session management with proper error handling and cleanup
  - ✅ Unit tests with 100% coverage for models, config, and database layers
  - ✅ CLI interface for database initialization and health checks
- [ ] Implement RSS feed fetcher with feedparser integration and unit tests
- [ ] Create website scraper with BeautifulSoup for content extraction and unit tests

### Phase 2: Service Features  
- [ ] Add error handling, retry logic, and rate limiting utilities with unit tests
- [ ] Build core fetcher service with concurrent processing and unit tests
- [ ] Create health check API and CLI interface with unit tests

### Phase 3: Integration & Deployment
- [ ] Add integration tests for end-to-end workflows
- [ ] Implement monitoring, logging, and production deployment

## Implementation Details

### Completed: Database Models & Configuration

The foundation layer has been implemented with the following components:

#### Database Models (`app/models.py`)
- **Source Model**: Manages RSS feeds and website sources with error tracking
  - URL validation, fetch status tracking, auto-disable on failures
  - Methods: `is_healthy()`, `update_fetch_success()`, `update_fetch_error()`
- **Article Model**: Stores fetched news articles with metadata
  - Deduplication by URL, flexible content storage
  - Methods: `exists_by_url()`, `create_from_dict()`
- **FetchLog Model**: Tracks fetch operations for monitoring
  - Performance metrics, error logging, duration tracking
  - Methods: `mark_completed()`

#### Configuration Management (`app/config.py`)
- Pydantic-based settings with environment variable support
- Development and production database configurations
- Configurable rate limiting, timeouts, and error thresholds
- Environment prefix: `FETCHER_*`

#### Database Layer (`app/database.py`)
- SQLAlchemy engine with SQLite/PostgreSQL support
- Session management with proper cleanup and error handling
- Connection testing and table creation utilities
- Functions: `get_database_session()`, `create_database_tables()`, `test_database_connection()`

#### CLI Interface (`app/main.py`)
- Database initialization: `python -m app.main --init-db`
- Health checks: `python -m app.main --health`
- Configurable logging levels
- Service status monitoring

#### Testing (`tests/`)
- **22 unit tests** covering all components with 100% pass rate
- Database models, configuration validation, session management
- Mock-based testing for database operations
- Test database isolation using in-memory SQLite

### Dependencies Added
```
pydantic-settings==2.1.0  # Configuration management
```

### Usage Examples

```bash
# Install dependencies in conda environment
conda create -n fetcher-env python=3.11
conda activate fetcher-env
pip install -r requirements.txt

# Initialize database
python -m app.main --init-db

# Run health check
python -m app.main --health

# Run tests
python -m pytest tests/ -v
```