// ==========================================
// ProjectForm — Create / Edit project modal body
// ==========================================
import { useState } from 'react'

const STATUS_OPTIONS = [
  { value: 'active',    label: 'Активный' },
  { value: 'archived',  label: 'Архив' },
  { value: 'completed', label: 'Завершён' },
]

export default function ProjectForm({ initial = {}, onSubmit, loading }) {
  const [form, setForm] = useState({
    name:        initial.name        ?? '',
    description: initial.description ?? '',
    status:      initial.status      ?? 'active',
  })

  const set = (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))

  function handleSubmit(e) {
    e.preventDefault()
    if (!form.name.trim()) return
    onSubmit(form)
  }

  return (
    <form id="project-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label className="form-label" htmlFor="proj-name">Название проекта *</label>
        <input
          id="proj-name"
          className="form-input"
          placeholder="Например: ЭРА — Единая Розничная Аналитика"
          value={form.name}
          onChange={set('name')}
          required
          autoFocus
        />
      </div>

      <div className="form-group" style={{ marginTop: '16px' }}>
        <label className="form-label" htmlFor="proj-desc">Описание</label>
        <textarea
          id="proj-desc"
          className="form-textarea"
          placeholder="Краткое описание цели и масштаба проекта..."
          value={form.description}
          onChange={set('description')}
          rows={4}
        />
      </div>

      <div className="form-group" style={{ marginTop: '16px' }}>
        <label className="form-label" htmlFor="proj-status">Статус</label>
        <select
          id="proj-status"
          className="form-select"
          value={form.status}
          onChange={set('status')}
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>
    </form>
  )
}
