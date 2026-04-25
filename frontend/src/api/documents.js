import client from './client'

// ==========================================
// Documents API
// ==========================================

export const getDocumentsByProject = (projectId)        => client.get(`/projects/${projectId}/documents`)
export const getDocumentById       = (id)               => client.get(`/documents/${id}`)
export const createDocument        = (projectId, data)  => client.post(`/projects/${projectId}/documents`, data)
export const deleteDocument        = (id)               => client.delete(`/documents/${id}`)
