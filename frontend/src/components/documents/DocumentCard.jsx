// ==========================================
// DocumentCard — Document list item
// ==========================================
import { DocTypeBadge } from '../ui/Badge'

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function DocumentCard({ doc, onDelete }) {
  function handleDelete() {
    if (window.confirm(`Удалить документ «${doc.title}»?`)) onDelete(doc.id)
  }

  return (
    <div className="doc-card">
      <div className="doc-card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <span className="doc-card-title">{doc.title}</span>
          <DocTypeBadge type={doc.doc_type} />
        </div>
        <button
          className="btn btn-ghost btn-sm"
          onClick={handleDelete}
          title="Удалить документ"
          style={{ color: 'var(--danger)', opacity: 0.7, flexShrink: 0 }}
        >
          ✕
        </button>
      </div>

      <div className="doc-card-meta">
        📎 Загружен: {formatDate(doc.uploaded_at)}
        &nbsp;·&nbsp;
        {doc.content.length.toLocaleString()} символов
      </div>

      <p className="doc-card-preview">{doc.content}</p>
    </div>
  )
}
