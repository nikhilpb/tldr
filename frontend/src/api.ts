import { Source, Article, ArticlesResponse, CreateSourceRequest, UpdateSourceRequest } from './types';

const API_BASE = '/api/v1';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new ApiError(response.status, errorText || response.statusText);
  }

  return response.json();
}

export const api = {
  // Sources
  async getSources(): Promise<Source[]> {
    const response = await fetchApi<{ sources: Source[]; total: number }>('/sources');
    return response.sources;
  },

  async getSource(id: number): Promise<Source> {
    return fetchApi(`/sources/${id}`);
  },

  async createSource(data: CreateSourceRequest): Promise<Source> {
    return fetchApi('/sources', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updateSource(id: number, data: UpdateSourceRequest): Promise<Source> {
    return fetchApi(`/sources/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async deleteSource(id: number): Promise<void> {
    return fetchApi(`/sources/${id}`, {
      method: 'DELETE',
    });
  },

  // Articles
  async getArticles(params?: {
    days_back?: number;
    limit?: number;
    offset?: number;
    source_id?: number;
    sort?: 'newest' | 'oldest';
  }): Promise<ArticlesResponse> {
    const searchParams = new URLSearchParams();
    if (params?.days_back) searchParams.set('days_back', params.days_back.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());
    if (params?.source_id) searchParams.set('source_id', params.source_id.toString());
    if (params?.sort) searchParams.set('sort', params.sort);

    const query = searchParams.toString();
    return fetchApi(`/articles${query ? `?${query}` : ''}`);
  },

  async getArticle(id: number): Promise<Article> {
    return fetchApi(`/articles/${id}`);
  },

  // System
  async refreshSources(): Promise<void> {
    return fetchApi('/refresh', { method: 'POST' });
  },
}; 