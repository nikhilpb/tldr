# Engineering Design Document: News Aggregator App

## System Architecture Overview

The news aggregator application follows a microservices-inspired architecture with the following high-level design:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Content       │
│   (Web App)     │◄──►│   Service       │◄──►│   Fetcher       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Database      │    │   Scheduler     │
                       │   Layer         │    │   Service       │
                       └─────────────────┘    └─────────────────┘
```

## Key Components

### 1. Frontend Web Application
**Responsibility**: User interface for managing sources and viewing aggregated content
- Source management (add/remove/enable/disable sources)
- Article browsing with search and filtering
- Article detail view
- Responsive design for desktop and mobile

### 2. Backend API Service
**Responsibility**: Core business logic and data management
- RESTful API endpoints for source management
- Article retrieval and search APIs
- Content aggregation orchestration
- Request validation and error handling

### 3. Content Fetcher Service
**Responsibility**: Fetching and parsing content from various sources
- RSS/Atom feed parsing
- Web scraping for blog-style sources
- Content extraction and normalization
- Error handling for failed fetches
- Rate limiting and respectful crawling

### 4. Scheduler Service
**Responsibility**: Orchestrating periodic content updates
- Hourly content refresh from all active sources
- Retry logic for failed fetches
- Cleanup of old articles (1-year retention)
- Health monitoring of sources

### 5. Database Layer
**Responsibility**: Data persistence and retrieval
- Source configuration storage
- Article metadata and content storage
- User preferences (local)
- Search indexing

## Technology Stack Recommendations

### Programming Language Options

#### Option 1: Python (Recommended)
**Pros:**
- Excellent ecosystem for web scraping (BeautifulSoup, Scrapy)
- Strong RSS parsing libraries (feedparser)
- Rich web frameworks (FastAPI, Flask)
- Great for data processing and NLP
- Large community and documentation

**Cons:**
- Potentially slower than compiled languages
- GIL limitations for CPU-intensive tasks

**Recommended Libraries:**
- **Web Framework**: FastAPI (modern, fast, automatic API docs)
- **Web Scraping**: BeautifulSoup4 + requests, Scrapy for complex sites
- **RSS Parsing**: feedparser
- **Database ORM**: SQLAlchemy + Alembic
- **Task Scheduling**: APScheduler or Celery
- **Testing**: pytest

#### Option 2: Node.js
**Pros:**
- Single language for frontend and backend
- Excellent performance for I/O operations
- Rich ecosystem (npm)
- Good for real-time features

**Cons:**
- Less mature web scraping ecosystem
- Single-threaded limitations
- Callback complexity

#### Option 3: Go
**Pros:**
- Excellent performance and concurrency
- Small binary size for containers
- Strong standard library

**Cons:**
- Smaller ecosystem for web scraping
- Steeper learning curve

### Database Options

#### Option 1: PostgreSQL (Recommended for Production)
**Pros:**
- Full-text search capabilities
- JSON support for flexible schemas
- Excellent performance and reliability
- Strong ecosystem and tooling

**Use Case**: Production deployment on GCP

#### Option 2: SQLite (Recommended for Local Development)
**Pros:**
- Zero configuration
- File-based, easy to backup
- Perfect for single-user applications
- Excellent for development and testing

**Use Case**: Local development and testing

#### Option 3: MongoDB
**Pros:**
- Flexible schema for varying article structures
- Built-in full-text search
- Good for unstructured content

**Cons:**
- Overkill for structured news data
- Additional operational complexity

### Frontend Options

#### Option 1: React + TypeScript (Recommended)
**Pros:**
- Large ecosystem and community
- Excellent developer experience
- Strong typing with TypeScript
- Component reusability

**Recommended Stack:**
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Library**: Material-UI or Tailwind CSS
- **State Management**: React Query for server state
- **Routing**: React Router

#### Option 2: Vue.js
**Pros:**
- Gentle learning curve
- Good performance
- Excellent documentation

#### Option 3: Server-Side Rendering (SSR)
**Pros:**
- Better SEO (though not critical for single-user app)
- Faster initial load
- Simpler deployment

**Options**: Next.js, Jinja2 templates with Flask

## Deployment Architecture

### Local Development (Docker Compose)

```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///app.db
    volumes:
      - ./data:/app/data
  
  scheduler:
    build: ./backend
    command: python scheduler.py
    depends_on:
      - backend
```

### Production Deployment on GCP

#### Option 1: Compute Engine + Docker (Recommended)
**Architecture:**
```
Internet → Cloud Load Balancer → Compute Engine Instance
                                      ↓
                                Cloud SQL (PostgreSQL)
                                      ↓
                                Cloud Storage (backups)
```

**Benefits:**
- More control over environment and resources
- Cost-effective for predictable workloads
- Familiar VM-based deployment
- Simple scaling through instance groups if needed
- Direct access to logs and monitoring

**Setup:**
- **Instance Type**: e2-medium (2 vCPU, 4GB memory)
- **OS**: Container-Optimized OS (COS)
- **Networking**: VPC with private subnet
- **Startup Script**: Docker Compose automation
- **Instance Templates**: For consistent deployments

**Services Running on VM:**
- Docker Compose orchestration
- Frontend container (nginx + React)
- Backend API container (FastAPI)
- Content Fetcher container
- Scheduler container
- Monitoring agent

#### Option 2: Cloud Run
**Benefits:**
- Serverless, pay-per-use
- Automatic scaling
- Zero infrastructure management

**Drawbacks:**
- Less control over runtime environment
- Could be more expensive for constant workloads
- More complex service coordination

#### Option 3: Google Kubernetes Engine (GKE)
**Benefits:**
- Advanced orchestration capabilities
- Auto-scaling and self-healing
- Good for future multi-user scaling

**Drawbacks:**
- Overkill for single-user v1
- Higher operational complexity
- More expensive for small deployments

## Docker Configuration

### Multi-Stage Dockerfile (Backend)
```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile
```dockerfile
# Build stage
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Data Models

### Sources Table
```sql
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    url VARCHAR(512) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'rss' or 'website'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_fetched_at TIMESTAMP,
    fetch_error_count INTEGER DEFAULT 0
);
```

### Articles Table
```sql
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id),
    title VARCHAR(512) NOT NULL,
    url VARCHAR(512) NOT NULL UNIQUE,
    author VARCHAR(255),
    published_at TIMESTAMP,
    summary TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Full-text search index
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', title || ' ' || COALESCE(summary, '') || ' ' || COALESCE(content, ''))
    ) STORED
);

-- Indexes for performance
CREATE INDEX idx_articles_published_at ON articles(published_at DESC);
CREATE INDEX idx_articles_source_id ON articles(source_id);
CREATE INDEX idx_articles_search ON articles USING GIN(search_vector);
```

## API Design

### RESTful Endpoints

```
Sources Management:
GET    /api/sources              # List all sources
POST   /api/sources              # Add new source
PUT    /api/sources/{id}         # Update source
DELETE /api/sources/{id}         # Delete source

Articles:
GET    /api/articles             # List articles with pagination
GET    /api/articles/search      # Search articles
GET    /api/articles/{id}        # Get article details

System:
POST   /api/refresh              # Trigger manual refresh
GET    /api/health               # Health check
```

## Security Considerations

### For Single-User V1:
- Input validation and sanitization
- Rate limiting on API endpoints
- CORS configuration
- SQL injection prevention (parameterized queries)
- XSS prevention in content display

### For Production:
- HTTPS termination at load balancer
- Content Security Policy (CSP)
- Secure headers
- Regular security updates
- Database connection encryption

## Performance Considerations

### Caching Strategy:
- Redis for API response caching (optional)
- Database query optimization
- CDN for static assets (GCP Cloud CDN)

### Scaling Approach:
- Horizontal scaling of Cloud Run services
- Database connection pooling
- Async processing for content fetching
- Pagination for large article lists

## Development Workflow

### Local Setup:
1. Clone repository
2. `docker-compose up` for full stack
3. Database migrations automatically applied
4. Hot reloading for development

### CI/CD Pipeline (GitHub Actions + GCP):
```yaml
# .github/workflows/deploy.yml
name: Deploy to GCP
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v0
      - name: Build and Deploy
        run: |
          gcloud builds submit --tag gcr.io/$PROJECT_ID/news-aggregator
          gcloud run deploy --image gcr.io/$PROJECT_ID/news-aggregator
```

## Monitoring and Observability

### GCP Native Solutions:
- **Logging**: Cloud Logging for application logs
- **Monitoring**: Cloud Monitoring for metrics
- **Alerting**: Cloud Monitoring alerts for service health
- **Tracing**: Cloud Trace for request tracing

### Key Metrics to Monitor:
- API response times and error rates
- Content fetch success/failure rates
- Database performance
- Storage usage
- Memory and CPU utilization

## Cost Estimation (GCP)

### Development Environment:
- Cloud Run: ~$0 (free tier)
- Cloud SQL (small instance): ~$10/month
- Cloud Storage: ~$1/month
- **Total: ~$11/month**

### Production Environment:
- Cloud Run: ~$20-50/month (depending on usage)
- Cloud SQL (production instance): ~$50-100/month
- Cloud Storage: ~$5/month
- Load Balancer: ~$20/month
- **Total: ~$95-175/month**

## Next Steps

1. **Phase 1**: Set up development environment with Docker
2. **Phase 2**: Implement core backend API with FastAPI
3. **Phase 3**: Build content fetcher service
4. **Phase 4**: Develop frontend application
5. **Phase 5**: Deploy to GCP Cloud Run
6. **Phase 6**: Set up monitoring and CI/CD

This design provides a solid foundation for the v1 news aggregator while maintaining flexibility for future enhancements and scaling. 