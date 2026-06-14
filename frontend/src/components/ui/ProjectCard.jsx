// ==========================================
// ProjectCard — Dashboard project card
// Includes GaugeChart for risk/profitability
// ==========================================
import { Link } from 'react-router-dom'
import GaugeChart from './GaugeChart'

const STATUS_STYLES = {
  active:    { bg: 'bg-emerald/10', text: 'text-emerald', dot: 'bg-emerald', label: 'Active' },
  completed: { bg: 'bg-electric/10', text: 'text-electric', dot: 'bg-electric', label: 'Completed' },
  archived:  { bg: 'bg-gray-500/10', text: 'text-gray-400', dot: 'bg-gray-500', label: 'Archived' },
}

export default function ProjectCard({ project, onDelete }) {
  const status = STATUS_STYLES[project.status] || STATUS_STYLES.active

  // Use database-fetched NLP scores, fallback to 0
  const risk = project.risk_score ?? 0
  const profit = project.profitability_score ?? 0

  return (
    <div className="group relative bg-surface border border-white/5 rounded-2xl p-6 hover:border-electric/20 transition-all duration-500 hover:shadow-[0_0_40px_rgba(0,240,255,0.04)]">
      {/* --- Header --- */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <Link
            to={`/projects/${project.id}`}
            className="text-lg font-semibold text-white hover:text-electric transition-colors"
          >
            {project.name}
          </Link>
          <p className="text-sm text-gray-500 mt-1 line-clamp-2">{project.description || 'No description'}</p>
        </div>
        <span className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold uppercase tracking-wider ${status.bg} ${status.text}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`} />
          {status.label}
        </span>
      </div>

      {/* --- Gauge charts --- */}
      <div className="flex items-center justify-around py-4 border-t border-b border-white/5">
        <GaugeChart value={risk} label="Risk Level" color="#FF3366" size={100} />
        <GaugeChart value={profit} label="Profitability" color="#00FF66" size={100} />
      </div>

      {/* --- Footer --- */}
      <div className="flex items-center justify-between mt-4">
        <span className="text-xs text-gray-600">
          {new Date(project.created_at).toLocaleDateString('ru-RU')}
        </span>
        <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <Link
            to={`/projects/${project.id}`}
            className="text-xs px-3 py-1.5 rounded-lg bg-electric/10 text-electric hover:bg-electric/20 transition-colors"
          >
            Open →
          </Link>
          {onDelete && (
            <button
              onClick={() => onDelete(project.id)}
              className="text-xs px-3 py-1.5 rounded-lg bg-crimson/10 text-crimson hover:bg-crimson/20 transition-colors"
            >
              Delete
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
