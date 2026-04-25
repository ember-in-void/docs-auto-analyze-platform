import { useState, useEffect, useCallback } from 'react'
import { getDocumentsByProject, createDocument, deleteDocument } from '../api/documents'

// ==========================================
// useDocuments — Custom Hook
// ==========================================
export function useDocuments(projectId) {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)

  const fetchAll = useCallback(async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      const data = await getDocumentsByProject(projectId)
      setDocuments(data ?? [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => { fetchAll() }, [fetchAll])

  const create = useCallback(async (payload) => {
    const created = await createDocument(projectId, payload)
    setDocuments((prev) => [created, ...prev])
    return created
  }, [projectId])

  const remove = useCallback(async (id) => {
    await deleteDocument(id)
    setDocuments((prev) => prev.filter((d) => d.id !== id))
  }, [])

  return { documents, loading, error, refetch: fetchAll, create, remove }
}
