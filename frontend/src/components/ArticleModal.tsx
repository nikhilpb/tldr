import { Article } from '../types';

interface ArticleModalProps {
  article: Article;
  onClose: () => void;
}

export default function ArticleModal({ article, onClose }: ArticleModalProps) {
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown date';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const stripImages = (html: string): string => {
    // Remove images, videos, audio, and other media elements
    return html
      .replace(/<img[^>]*>/gi, '') // Remove img tags
      .replace(/<video[^>]*>.*?<\/video>/gi, '') // Remove video tags
      .replace(/<audio[^>]*>.*?<\/audio>/gi, '') // Remove audio tags
      .replace(/<iframe[^>]*>.*?<\/iframe>/gi, '') // Remove iframe tags
      .replace(/<svg[^>]*>.*?<\/svg>/gi, '') // Remove svg tags
      .replace(/<figure[^>]*>.*?<\/figure>/gi, '') // Remove figure tags (often contain images)
      .replace(/<picture[^>]*>.*?<\/picture>/gi, '') // Remove picture tags
      .replace(/\s+/g, ' ') // Clean up extra whitespace
      .trim();
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal" style={{ maxWidth: '800px' }}>
        <div className="modal-header">
          <div>
            <h1 style={{ margin: 0, fontSize: '1.5rem', marginBottom: '0.5rem' }}>{article.title}</h1>
            {article.source_name && (
              <div style={{ 
                fontSize: '1rem', 
                fontWeight: '600', 
                color: '#3b82f6',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <span style={{ 
                  background: '#f0f9ff', 
                  padding: '0.25rem 0.75rem', 
                  borderRadius: '1rem',
                  fontSize: '0.875rem'
                }}>
                  {article.source_name}
                </span>
              </div>
            )}
          </div>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="article-meta" style={{ marginBottom: '1.5rem' }}>
          <span>By {article.author || 'Unknown'}</span>
          <span>Published {formatDate(article.published_at)}</span>
          <a 
            href={article.url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="btn btn-secondary"
            style={{ marginLeft: 'auto' }}
          >
            Read Original
          </a>
        </div>

        <div className="article-content">
          {article.content ? (
            <div 
              dangerouslySetInnerHTML={{ __html: stripImages(article.content) }}
              style={{ lineHeight: '1.8' }}
            />
          ) : article.summary ? (
            <p>{article.summary}</p>
          ) : (
            <p style={{ fontStyle: 'italic', color: '#64748b' }}>
              No content available. Click "Read Original" to view the full article.
            </p>
          )}
        </div>
      </div>
    </div>
  );
} 