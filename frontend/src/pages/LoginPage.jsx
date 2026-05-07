// ==========================================
// LoginPage — Minimal dark login form
// ==========================================
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-navy">
      <div className="w-full max-w-md animate-slide-up">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-10">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-electric to-emerald flex items-center justify-center text-navy-dark font-bold">
            DA
          </div>
          <span className="text-xl font-bold">DocuAudit <span className="text-electric">AI</span></span>
        </div>

        <h1 className="text-2xl font-bold mb-2">Sign In</h1>
        <p className="text-sm text-gray-500 mb-8">Enter your credentials to access the platform.</p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs uppercase tracking-wider text-gray-500 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-surface border border-white/10 rounded-xl px-4 py-3.5 text-white text-sm focus:border-electric outline-none transition-colors"
              placeholder="you@company.com"
              required
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-wider text-gray-500 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-surface border border-white/10 rounded-xl px-4 py-3.5 text-white text-sm focus:border-electric outline-none transition-colors"
              placeholder="••••••••"
              required
            />
          </div>

          {error && (
            <div className="p-3 rounded-lg border border-crimson/20 bg-crimson/5 text-crimson text-sm">
              ⚠ {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl bg-electric text-navy-dark font-bold text-sm uppercase tracking-wider hover:shadow-[0_0_30px_rgba(0,240,255,0.3)] transition-all duration-500 disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-gray-500">
          Don't have an account?{' '}
          <Link to="/register" className="text-electric font-semibold hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  )
}
