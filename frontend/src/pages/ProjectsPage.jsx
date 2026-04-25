// ==========================================
// ProjectsPage — Main projects list view
// ==========================================
import { useState } from 'react'
import TopBar from '../components/layout/TopBar'
import ProjectCard from '../components/projects/ProjectCard'
import ProjectForm from '../components/projects/ProjectForm'
import Modal from '../components/ui/Modal'
import Spinner from '../components/ui/Spinner'
import EmptyState from '../components/ui/EmptyState'
import { useProjects } from '../hooks/useProjects'

const STATUS_FILTERS = [
  { value: 'all',       label: 'Все' },
  { value: 'active',    label: 'Активные' },
  { value: 'completed', label: 'Завершённые' },
  { value: 'archived',  label: 'Архив' },
]

export default function ProjectsPage() {
  const { projects, loading, error, create, remove } = useProjects()
  const [showModal, setShowModal]   = useState(false)
  const [saving, setSaving]         = useState(false)
  const [filter, setFilter]         = useState('all')
  const [formError, setFormError]   = useState(null)

  // --- Derived ---
  const filtered = filter === 'all'
    ? projects
    : projects.filter((p) => p.status === filter)

  const counts = {
    active:    projects.filter((p) => p.status === 'active').length,
    completed: projects.filter((p) => p.status === 'completed').length,
    archived:  projects.filter((p) => p.status === 'archived').length,
  }

  // --- Handlers ---
  async function handleCreate(formData) {
    setSaving(true)
    setFormError(null)
    try {
      await create(formData)
      setShowModal(false)
    } catch (err) {
      setFormError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <TopBar
        title="Проекты"
        breadcrumb="Список всех ИТ-проектов"
        actions={
          <button className="btn btn-primary" id="btn-new-project" onClick={() => setShowModal(true)}>
            + Новый проект
          </button>
        }
      />

      <div className="page">
        {/* Stats */}
        <div className="stats-row">
          <div className="stat-card">
            <div className="stat-label">Всего проектов</div>
            <div className="stat-value">{projects.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Активных</div>
            <div className="stat-value" style={{ color: 'var(--success)' }}>{counts.active}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Завершённых</div>
            <div className="stat-value" style={{ color: 'var(--info)' }}>{counts.completed}</div>
          </div>
        </div>

        {/* Filter tabs */}
        <div className="tabs">
          {STATUS_FILTERS.map(({ value, label }) => (
            <button
              key={value}
              id={`tab-filter-${value}`}
              className={`tab${filter === value ? ' active' : ''}`}
              onClick={() => setFilter(value)}
            >
              {label}
              <span className="tab-count">
                {value === 'all' ? projects.length : (counts[value] ?? 0)}
              </span>
            </button>
          ))}
        </div>

        {/* Content */}
        {loading && <Spinner />}

        {error && (
          <div style={{ color: 'var(--danger)', padding: '16px', background: 'var(--danger-dim)', borderRadius: 'var(--radius)', marginBottom: 16 }}>
            ⚠ Ошибка загрузки: {error}
          </div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <EmptyState
            icon="📋"
            title="Проекты не найдены"
            description={filter === 'all' ? 'Создайте первый проект, чтобы начать работу.' : `Проектов со статусом «${filter}» нет.`}
            action={
              filter === 'all' && (
                <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                  + Создать проект
                </button>
              )
            }
          />
        )}

        {!loading && filtered.length > 0 && (
          <div className="grid grid-2">
            {filtered.map((p) => (
              <ProjectCard key={p.id} project={p} onDelete={remove} />
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showModal && (
        <Modal
          title="Новый проект"
          onClose={() => { setShowModal(false); setFormError(null) }}
          footer={
            <>
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Отмена</button>
              <button
                className="btn btn-primary"
                form="project-form"
                type="submit"
                disabled={saving}
              >
                {saving ? 'Создание...' : 'Создать'}
              </button>
            </>
          }
        >
          <ProjectForm onSubmit={handleCreate} loading={saving} />
          {formError && (
            <div style={{ color: 'var(--danger)', fontSize: 12, marginTop: 8 }}>⚠ {formError}</div>
          )}
        </Modal>
      )}
    </>
  )
}
