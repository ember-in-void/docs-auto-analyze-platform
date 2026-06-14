// ==========================================
// Axios Instance — API Client for DocuAudit AI
// ==========================================
import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000,
})

// --- Request interceptor: attach JWT token ---
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// --- Response interceptor: unwrap { data: ... } envelope ---
client.interceptors.response.use(
  (response) => {
    if (response.data && Object.prototype.hasOwnProperty.call(response.data, 'data')) {
      return response.data.data
    }
    return response.data
  },
  (error) => {
    const msg = error.response?.data?.error ?? error.message ?? 'Неизвестная ошибка'
    return Promise.reject(new Error(msg))
  }
)

export default client
