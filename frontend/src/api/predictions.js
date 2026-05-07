// ==========================================
// Predictions API — Generate & List
// ==========================================
import client from './client'

export const getPredictions = (projectId) =>
  client.get(`/projects/${projectId}/predictions`)

export const generatePrediction = (projectId) =>
  client.post(`/projects/${projectId}/predictions/generate`)
