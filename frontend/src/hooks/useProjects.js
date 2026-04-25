import { useState, useEffect, useCallback } from 'react'
import { getProjects, createProject, updateProject, deleteProject } from '../api/projects'

// ==========================================
// useProjects — Custom Hook
// ==========================================
export function useProjects() {
  const [projects, setProjects]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getProjects()
      setProjects(data ?? [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchAll() }, [fetchAll])

  const create = useCallback(async (payload) => {
    const created = await createProject(payload)
    setProjects((prev) => [created, ...prev])
    return created
  }, [])

  const update = useCallback(async (id, payload) => {
    const updated = await updateProject(id, payload)
    setProjects((prev) => prev.map((p) => (p.id === id ? updated : p)))
    return updated
  }, [])

  const remove = useCallback(async (id) => {
    await deleteProject(id)
    setProjects((prev) => prev.filter((p) => p.id !== id))
  }, [])

  return { projects, loading, error, refetch: fetchAll, create, update, remove }
}
