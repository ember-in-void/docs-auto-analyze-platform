// ==========================================
// useProjects — Custom hook for projects CRUD
// ==========================================
import { useState, useEffect, useCallback } from 'react'
import * as api from '../api/projects'

export function useProjects() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState(null)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.getProjects()
      setProjects(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const create = async (formData) => {
    const created = await api.createProject(formData)
    setProjects((prev) => [created, ...prev])
  }

  const remove = async (id) => {
    await api.deleteProject(id)
    setProjects((prev) => prev.filter((p) => p.id !== id))
  }

  return { projects, loading, error, create, remove, refresh: load }
}
