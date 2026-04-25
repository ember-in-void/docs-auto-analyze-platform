// ==========================================
// ProjectCard — Project list item
// ==========================================
import { useNavigate } from 'react-router-dom'
import { StatusBadge } from '../ui/Badge'

const STATUS_ICON = { active: '🟢', archived: '⚪', completed: '🔵' }

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

export default function ProjectCard({ project, onDelete }) {
  const navigate = useNavigate()

  function handleDelete(e) {
    e.stopPropagation()
    if (window.confirm(`Удалить проект «${project.name}»? Все документы и прогнозы будут удалены.`)) {
      onDelete(project.id)
    }
  }

  return (
    <div className="project-card" onClick={() => navigate(`/projects/${project.id}`)}>
      <div className="project-card-header">
        <h3 className="project-card-name">{project.name}</h3>
        <StatusBadge status={project.status} />
      </div>

      <p className="project-card-desc">
        {project.description || 'Описание не указано'}
      </p>

      <div className="project-card-footer">
        <div className="project-card-meta">
          <span className="project-card-stat">
            <span>📅</span> {formatDate(project.created_at)}
          </span>
        </div>
        <button
          className="btn btn-ghost btn-sm"
          onClick={handleDelete}
          title="Удалить проект"
          style={{ color: 'var(--danger)', opacity: 0.7 }}
        >
          ✕
        </button>
      </div>
    </div>
  )
}
