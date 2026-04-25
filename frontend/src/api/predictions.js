import client from './client'

// ==========================================
// Predictions API
// ==========================================

export const getPredictionsByProject = (projectId) => client.get(`/projects/${projectId}/predictions`)
export const generatePrediction      = (projectId) => client.post(`/projects/${projectId}/predictions/generate`)
