// ==========================================
// EmptyState — Placeholder for empty lists
// ==========================================

export default function EmptyState({ icon = '📂', title, description, action }) {
  return (
    <div className="empty-state">
      <span className="empty-state-icon">{icon}</span>
      <span className="empty-state-title">{title}</span>
      {description && <p className="empty-state-desc">{description}</p>}
      {action}
    </div>
  )
}
