import { useState } from 'react';
import { api } from '../api';
import { Source, CreateSourceRequest, UpdateSourceRequest } from '../types';

interface SourceModalProps {
  source?: Source; // If provided, we're editing; otherwise, creating
  onClose: () => void;
  onSaved: () => void;
}

export default function SourceModal({ source, onClose, onSaved }: SourceModalProps) {
  const [formData, setFormData] = useState({
    name: source?.name || '',
    url: source?.url || '',
    type: source?.type || 'rss' as 'rss' | 'website',
    is_active: source?.is_active ?? true,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim() || !formData.url.trim()) {
      setError('Name and URL are required');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      if (source) {
        // Editing existing source
        const updateData: UpdateSourceRequest = {};
        if (formData.name !== source.name) updateData.name = formData.name;
        if (formData.url !== source.url) updateData.url = formData.url;
        if (formData.type !== source.type) updateData.type = formData.type;
        if (formData.is_active !== source.is_active) updateData.is_active = formData.is_active;

        await api.updateSource(source.id, updateData);
      } else {
        // Creating new source
        const createData: CreateSourceRequest = {
          name: formData.name,
          url: formData.url,
          type: formData.type,
          is_active: formData.is_active,
        };
        await api.createSource(createData);
      }

      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save source');
    } finally {
      setLoading(false);
    }
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal" style={{ maxWidth: '500px' }}>
        <div className="modal-header">
          <h2 style={{ margin: 0 }}>
            {source ? 'Edit Source' : 'Add New Source'}
          </h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="name">
              Name
            </label>
            <input
              type="text"
              id="name"
              className="form-input"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., TechCrunch"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="url">
              URL
            </label>
            <input
              type="url"
              id="url"
              className="form-input"
              value={formData.url}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              placeholder="e.g., https://feeds.feedburner.com/techcrunch"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="type">
              Type
            </label>
            <select
              id="type"
              className="form-select"
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value as 'rss' | 'website' })}
            >
              <option value="rss">RSS Feed</option>
              <option value="website">Website</option>
            </select>
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              />
              Active
            </label>
          </div>

          <div className="form-actions">
            <button 
              type="button" 
              className="btn btn-secondary" 
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Saving...' : source ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 