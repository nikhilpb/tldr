-- Initial database schema for News Aggregator
-- This schema matches the SQLAlchemy models in fetcher/app/models.py

CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    url VARCHAR(512) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'rss' or 'website'
    is_active BOOLEAN DEFAULT true NOT NULL,
    
    -- Timestamps (timezone-aware)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_fetched_at TIMESTAMP WITH TIME ZONE,
    
    -- Error tracking
    fetch_error_count INTEGER DEFAULT 0 NOT NULL,
    last_error_message TEXT,
    last_error_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id) NOT NULL,
    
    -- Article metadata
    title VARCHAR(512) NOT NULL,
    url VARCHAR(512) NOT NULL UNIQUE,
    author VARCHAR(255),
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Article content
    summary TEXT,
    content TEXT,
    
    -- Fetcher metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for performance (matches SQLAlchemy model indexes)
CREATE INDEX idx_sources_url ON sources(url);
CREATE INDEX idx_sources_is_active ON sources(is_active);
CREATE INDEX idx_articles_source_id ON articles(source_id);
CREATE INDEX idx_articles_url ON articles(url);
CREATE INDEX idx_articles_published_at ON articles(published_at DESC);

-- Insert some sample data for development
INSERT INTO sources (url, name, type) VALUES 
('https://feeds.feedburner.com/oreilly/radar/feed', 'O''Reilly Radar', 'rss'),
('https://www.theverge.com/rss/index.xml', 'The Verge', 'rss');