// ==========================================
// usePredictions — Hook for NLP analysis
// ==========================================
import { useState, useEffect, useCallback } from 'react'
import * as api from '../api/predictions'

export function usePredictions(projectId) {
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading]        = useState(true)
  const [generating, setGenerating]  = useState(false)

  const load = useCallback(async () => {
    if (!projectId) return
    try {
      setLoading(true)
      const data = await api.getPredictions(projectId)
      setPredictions(Array.isArray(data) ? data : [])
    } catch {
      setPredictions([])
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => { load() }, [load])

  const generate = async () => {
    setGenerating(true)
    try {
      const result = await api.generatePrediction(projectId)
      setPredictions((prev) => [result, ...prev])
      return result
    } finally {
      setGenerating(false)
    }
  }

  return { predictions, loading, generating, generate, refresh: load }
}
