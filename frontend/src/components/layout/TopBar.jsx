// ==========================================
// TopBar — Fixed top header
// ==========================================

export default function TopBar({ title, breadcrumb, actions }) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <span className="topbar-title">{title}</span>
        {breadcrumb && <span className="topbar-breadcrumb">{breadcrumb}</span>}
      </div>
      {actions && <div className="topbar-right">{actions}</div>}
    </header>
  )
}
