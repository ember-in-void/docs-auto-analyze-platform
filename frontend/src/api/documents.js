// ==========================================
// Documents API — Upload & List
// ==========================================
import client from './client'

export const getDocuments = (projectId) =>
  client.get(`/projects/${projectId}/documents`)

export const getDocumentById = (id) =>
  client.get(`/documents/${id}`)

/**
 * createDocument uploads a file or JSON text to a project.
 * Accepts FormData (multipart) or plain object.
 */
export async function createDocument(projectId, payload) {
  // If payload is FormData (file upload) — override Content-Type
  if (payload instanceof FormData) {
    return client.post(`/projects/${projectId}/documents`, payload, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  }
  return client.post(`/projects/${projectId}/documents`, payload)
}

export const deleteDocument = (id) =>
  client.delete(`/documents/${id}`)
