// ==========================================
// Navbar — Top navigation bar with mobile hamburger
// ==========================================
import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const NAV_LINKS = [
  { to: '/',              label: 'Home' },
  { to: '/dashboard',     label: 'Dashboard' },
  { to: '/workspace',     label: 'Workspace' },
  { to: '/architecture',  label: 'Architecture' },
]

export default function Navbar() {
  const [open, setOpen] = useState(false)
  const { user, logout } = useAuth()
  const location = useLocation()

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* --- Logo --- */}
        <Link to="/" className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-electric to-emerald flex items-center justify-center text-navy-dark font-bold text-sm">
            DA
          </div>
          <span className="text-lg font-bold tracking-tight">
            Docu<span className="text-electric">Audit</span>
          </span>
        </Link>

        {/* --- Desktop nav --- */}
        <div className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors duration-300 ${
                location.pathname === to
                  ? 'text-electric bg-electric/10'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {label}
            </Link>
          ))}
        </div>

        {/* --- Auth section --- */}
        <div className="hidden md:flex items-center gap-3">
          {user ? (
            <>
              <span className="text-sm text-gray-400">{user.full_name}</span>
              <button
                onClick={logout}
                className="text-sm px-4 py-2 rounded-lg border border-white/10 text-gray-300 hover:bg-white/5 transition-colors"
              >
                Выйти
              </button>
            </>
          ) : (
            <Link
              to="/login"
              className="text-sm px-5 py-2 rounded-lg bg-electric text-navy-dark font-semibold hover:bg-electric/90 transition-colors"
            >
              Get Started
            </Link>
          )}
        </div>

        {/* --- Hamburger (mobile) --- */}
        <button
          className="md:hidden flex flex-col gap-1.5 p-2"
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
        >
          <span className={`w-6 h-0.5 bg-white transition-transform duration-300 ${open ? 'rotate-45 translate-y-2' : ''}`} />
          <span className={`w-6 h-0.5 bg-white transition-opacity duration-300 ${open ? 'opacity-0' : ''}`} />
          <span className={`w-6 h-0.5 bg-white transition-transform duration-300 ${open ? '-rotate-45 -translate-y-2' : ''}`} />
        </button>
      </div>

      {/* --- Mobile menu --- */}
      {open && (
        <div className="md:hidden bg-surface border-t border-white/5 px-6 pb-6 animate-slide-up">
          {NAV_LINKS.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className="block py-3 text-gray-300 hover:text-electric transition-colors border-b border-white/5"
            >
              {label}
            </Link>
          ))}
          {user ? (
            <button onClick={() => { logout(); setOpen(false) }} className="mt-4 text-sm text-crimson">
              Выйти
            </button>
          ) : (
            <Link to="/login" onClick={() => setOpen(false)} className="mt-4 block text-electric font-semibold">
              Get Started →
            </Link>
          )}
        </div>
      )}
    </nav>
  )
}
