export interface Source {
  id: number;
  url: string;
  name: string;
  type: 'rss' | 'website';
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_fetched_at?: string;
  fetch_error_count: number;
  last_error_message?: string;
  last_error_at?: string;
  article_count?: number;
}

export interface Article {
  id: number;
  source_id: number;
  title: string;
  url: string;
  author?: string;
  published_at?: string;
  summary?: string;
  content?: string;
  created_at: string;
  source_name?: string;
}

export interface ArticlesResponse {
  articles: Article[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface CreateSourceRequest {
  url: string;
  name: string;
  type: 'rss' | 'website';
  is_active?: boolean;
}

export interface UpdateSourceRequest {
  url?: string;
  name?: string;
  type?: 'rss' | 'website';
  is_active?: boolean;
} 