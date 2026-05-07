// ==========================================
// DashboardPage — Project portfolio grid
// ==========================================
import { useState } from 'react'
import ProjectCard from '../components/ui/ProjectCard'
import Modal from '../components/ui/Modal'
import { useProjects } from '../hooks/useProjects'

// --- Mock projects for demo (used when API returns empty) ---
const MOCK_PROJECTS = [
  { id: 'mock-1', name: 'CRM Migration Spec', description: 'Full migration plan for legacy CRM to cloud-native Salesforce integration.', status: 'active', created_at: '2026-04-15T10:00:00Z' },
  { id: 'mock-2', name: 'Payment Gateway Architecture', description: 'Microservice design for PCI-DSS compliant payment processing system.', status: 'completed', created_at: '2026-03-22T08:30:00Z' },
  { id: 'mock-3', name: 'Data Lake Infrastructure', description: 'AWS S3 + Apache Spark pipeline for real-time analytics and ML training.', status: 'active', created_at: '2026-04-01T14:00:00Z' },
  { id: 'mock-4', name: 'Mobile App Refactor', description: 'React Native to Flutter migration with offline-first architecture.', status: 'archived', created_at: '2026-02-10T12:00:00Z' },
]

export default function DashboardPage() {
  const { projects, loading, error, create, remove } = useProjects()
  const [showModal, setShowModal] = useState(false)
  const [formData, setFormData]   = useState({ name: '', description: '', status: 'active' })
  const [saving, setSaving]       = useState(false)

  // Use real projects if available, otherwise show mock data
  const displayProjects = projects.length > 0 ? projects : MOCK_PROJECTS

  async function handleCreate(e) {
    e.preventDefault()
    setSaving(true)
    try {
      await create(formData)
      setShowModal(false)
      setFormData({ name: '', description: '', status: 'active' })
    } catch { /* handled in hook */ }
    finally { setSaving(false) }
  }

  return (
    <div className="min-h-screen pt-24 pb-16 px-6">
      <div className="max-w-7xl mx-auto">
        {/* --- Header --- */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-10">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Project Dashboard</h1>
            <p className="text-gray-400 mt-1">Monitor risk scores and profitability across all IT projects.</p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="px-6 py-3 rounded-xl bg-electric text-navy-dark font-bold text-sm uppercase tracking-wider hover:shadow-[0_0_30px_rgba(0,240,255,0.3)] transition-all duration-500 self-start"
          >
            + New Project
          </button>
        </div>

        {/* --- Loading state --- */}
        {loading && (
          <div className="flex justify-center py-20">
            <div className="w-10 h-10 border-2 border-electric/20 border-t-electric rounded-full animate-spin" />
          </div>
        )}

        {/* --- Error state --- */}
        {error && (
          <div className="p-4 rounded-xl border border-crimson/20 bg-crimson/5 text-crimson text-sm mb-6">
            ⚠ {error}
          </div>
        )}

        {/* --- Project Grid --- */}
        {!loading && (
          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
            {displayProjects.map((p) => (
              <ProjectCard key={p.id} project={p} onDelete={projects.length > 0 ? remove : null} />
            ))}
          </div>
        )}
      </div>

      {/* --- Create Project Modal --- */}
      {showModal && (
        <Modal
          title="New Project"
          onClose={() => setShowModal(false)}
          footer={
            <>
              <button onClick={() => setShowModal(false)} className="px-5 py-2.5 rounded-lg border border-white/10 text-gray-300 text-sm hover:bg-white/5 transition-colors">
                Cancel
              </button>
              <button onClick={handleCreate} disabled={saving} className="px-5 py-2.5 rounded-lg bg-electric text-navy-dark font-semibold text-sm hover:bg-electric/90 transition-colors disabled:opacity-50">
                {saving ? 'Creating...' : 'Create'}
              </button>
            </>
          }
        >
          <form id="project-form" onSubmit={handleCreate} className="space-y-5">
            <div>
              <label className="block text-xs uppercase tracking-wider text-gray-500 mb-2">Project Name</label>
              <input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full bg-navy border border-white/10 rounded-lg px-4 py-3 text-white text-sm focus:border-electric outline-none transition-colors"
                placeholder="e.g. CRM Migration Spec"
                required
              />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-wider text-gray-500 mb-2">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full bg-navy border border-white/10 rounded-lg px-4 py-3 text-white text-sm focus:border-electric outline-none transition-colors resize-none h-24"
                placeholder="Brief project description..."
              />
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
