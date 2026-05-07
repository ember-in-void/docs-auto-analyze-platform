// ==========================================
// Projects API — CRUD Operations
// ==========================================
import client from './client'

export const getProjects    = ()        => client.get('/projects')
export const getProjectById = (id)      => client.get(`/projects/${id}`)
export const createProject  = (data)    => client.post('/projects', data)
export const updateProject  = (id, data)=> client.put(`/projects/${id}`, data)
export const deleteProject  = (id)      => client.delete(`/projects/${id}`)
