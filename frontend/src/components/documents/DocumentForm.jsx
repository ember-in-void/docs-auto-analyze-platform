// ==========================================
// DocumentForm — Add document modal body
// ==========================================
import { useState } from 'react'

const DOC_TYPE_OPTIONS = [
  { value: 'TZ',           label: 'Техническое задание' },
  { value: 'ARCHITECTURE', label: 'Архитектурный документ' },
  { value: 'REQUIREMENTS', label: 'Требования' },
  { value: 'LOGS',         label: 'Журнал / Логи' },
  { value: 'OTHER',        label: 'Прочее' },
]

export default function DocumentForm({ onSubmit, loading }) {
  const [form, setForm] = useState({ title: '', content: '', doc_type: 'TZ' })

  const set = (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))

  function handleSubmit(e) {
    e.preventDefault()
    if (!form.title.trim() || !form.content.trim()) return
    onSubmit(form)
  }

  return (
    <form id="document-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label className="form-label" htmlFor="doc-title">Название документа *</label>
        <input
          id="doc-title"
          className="form-input"
          placeholder="Например: Техническое задание v1.2"
          value={form.title}
          onChange={set('title')}
          required
          autoFocus
        />
      </div>

      <div className="form-group" style={{ marginTop: '16px' }}>
        <label className="form-label" htmlFor="doc-type">Тип документа</label>
        <select
          id="doc-type"
          className="form-select"
          value={form.doc_type}
          onChange={set('doc_type')}
        >
          {DOC_TYPE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      <div className="form-group" style={{ marginTop: '16px' }}>
        <label className="form-label" htmlFor="doc-content">
          Содержимое документа *
          <span style={{ color: 'var(--text-muted)', fontWeight: 400, marginLeft: 8 }}>
            ({form.content.length} симв.)
          </span>
        </label>
        <textarea
          id="doc-content"
          className="form-textarea"
          placeholder="Вставьте или введите текст документа..."
          value={form.content}
          onChange={set('content')}
          rows={8}
          required
          style={{ minHeight: 160 }}
        />
      </div>
    </form>
  )
}
