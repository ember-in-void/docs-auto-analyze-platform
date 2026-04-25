import { useState, useEffect, useCallback } from 'react'
import { getPredictionsByProject, generatePrediction } from '../api/predictions'

// ==========================================
// usePredictions — Custom Hook
// ==========================================
export function usePredictions(projectId) {
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading]         = useState(true)
  const [generating, setGenerating]   = useState(false)
  const [error, setError]             = useState(null)

  const fetchAll = useCallback(async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      const data = await getPredictionsByProject(projectId)
      setPredictions(data ?? [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => { fetchAll() }, [fetchAll])

  const generate = useCallback(async () => {
    setGenerating(true)
    setError(null)
    try {
      const created = await generatePrediction(projectId)
      setPredictions((prev) => [created, ...prev])
      return created
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setGenerating(false)
    }
  }, [projectId])

  return { predictions, loading, generating, error, refetch: fetchAll, generate }
}
