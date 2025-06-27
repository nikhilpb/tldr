import { useState, useEffect } from 'react';
import { api } from '../api';
import { Source } from '../types';
import SourceModal from '../components/SourceModal';

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getSources();
      setSources(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sources');
    } finally {
      setLoading(false);
    }
  };

  const handleSourceSaved = () => {
    setSelectedSource(null);
    setShowCreateModal(false);
    loadSources();
  };

  const handleDeleteSource = async (source: Source) => {
    if (!confirm(`Are you sure you want to delete "${source.name}"? This will also delete all its articles.`)) {
      return;
    }

    try {
      await api.deleteSource(source.id);
      loadSources();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete source');
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return <div className="loading">Loading sources...</div>;
  }

  if (error) {
    return (
      <div>
        <div className="error">{error}</div>
        <button className="btn btn-primary" onClick={loadSources}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 className="page-title">Sources</h1>
        <button 
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
        >
          Add Source
        </button>
      </div>

      {sources.length === 0 ? (
        <div className="card">
          <p>No sources configured. Add your first source to get started!</p>
        </div>
      ) : (
        <div>
          {sources.map((source) => (
            <div 
              key={source.id} 
              className="card clickable"
              onClick={() => setSelectedSource(source)}
            >
              <div className="source-meta">
                <div>
                  <h2 className="source-name">{source.name}</h2>
                  <div className="source-url">{source.url}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span className={source.is_active ? 'status-active' : 'status-inactive'}>
                    {source.is_active ? 'Active' : 'Inactive'}
                  </span>
                  <button
                    className="btn btn-secondary"
                    style={{ marginLeft: '1rem' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteSource(source);
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
              
              <div className="source-stats">
                <span>Type: {source.type.toUpperCase()}</span>
                <span>Last fetched: {formatDate(source.last_fetched_at)}</span>
                <span>Errors: {source.fetch_error_count}</span>
                {source.last_error_message && (
                  <span style={{ color: '#dc2626' }}>
                    Last error: {source.last_error_message}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedSource && (
        <SourceModal 
          source={selectedSource}
          onClose={() => setSelectedSource(null)}
          onSaved={handleSourceSaved}
        />
      )}

      {showCreateModal && (
        <SourceModal 
          onClose={() => setShowCreateModal(false)}
          onSaved={handleSourceSaved}
        />
      )}
    </div>
  );
} 