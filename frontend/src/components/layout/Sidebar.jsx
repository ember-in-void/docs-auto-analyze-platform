// ==========================================
// Sidebar — Fixed left navigation
// ==========================================
import { NavLink, useLocation } from 'react-router-dom'

const navItems = [
  { to: '/',         icon: '◈', label: 'Проекты' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">⬡</div>
        <div className="sidebar-logo-text">
          <span className="sidebar-logo-name">NLP Platform</span>
          <span className="sidebar-logo-sub">IT Doc Analyzer</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Навигация</div>
        {navItems.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
          >
            <span className="sidebar-link-icon">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="sidebar-version">MVP v0.1 · mock-v1</div>
      </div>
    </aside>
  )
}
