// ==========================================
// useDocuments — Hook for project documents
// ==========================================
import { useState, useEffect, useCallback } from 'react'
import * as api from '../api/documents'

export function useDocuments(projectId) {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading]    = useState(true)

  const load = useCallback(async () => {
    if (!projectId) return
    try {
      setLoading(true)
      const data = await api.getDocuments(projectId)
      setDocuments(Array.isArray(data) ? data : [])
    } catch {
      setDocuments([])
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => { load() }, [load])

  const create = async (payload) => {
    const created = await api.createDocument(projectId, payload)
    setDocuments((prev) => [created, ...prev])
    return created
  }

  const remove = async (id) => {
    await api.deleteDocument(id)
    setDocuments((prev) => prev.filter((d) => d.id !== id))
  }

  return { documents, loading, create, remove, refresh: load }
}
