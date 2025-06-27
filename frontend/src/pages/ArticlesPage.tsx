import { useState, useEffect } from 'react';
import { api } from '../api';
import { Article } from '../types';
import ArticleModal from '../components/ArticleModal';

export default function ArticlesPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);

  useEffect(() => {
    loadArticles();
  }, []);

  const loadArticles = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getArticles({ 
        limit: 50,
        sort: 'newest' 
      });
      setArticles(response.articles);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load articles');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown date';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return <div className="loading">Loading articles...</div>;
  }

  if (error) {
    return (
      <div>
        <div className="error">{error}</div>
        <button className="btn btn-primary" onClick={loadArticles}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 className="page-title">Articles</h1>
      </div>

      {articles.length === 0 ? (
        <div className="card">
          <p>No articles found. Try adding some sources first!</p>
        </div>
      ) : (
        <div>
          {articles.map((article) => (
            <div 
              key={article.id} 
              className="card clickable"
              onClick={() => setSelectedArticle(article)}
            >
              <h2 className="article-title">{article.title}</h2>
                              <div className="article-meta">
                  {article.source_name && (
                    <span style={{ 
                      background: '#f0f9ff', 
                      color: '#3b82f6',
                      padding: '0.25rem 0.5rem', 
                      borderRadius: '0.375rem',
                      fontSize: '0.75rem',
                      fontWeight: '500'
                    }}>
                      {article.source_name}
                    </span>
                  )}
                  <span>By {article.author || 'Unknown'}</span>
                  <span>Published {formatDate(article.published_at)}</span>
                </div>
              {article.summary && (
                <p className="article-summary">{article.summary}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {selectedArticle && (
        <ArticleModal 
          article={selectedArticle}
          onClose={() => setSelectedArticle(null)}
        />
      )}
    </div>
  );
} 