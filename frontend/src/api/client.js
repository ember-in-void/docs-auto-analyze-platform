// Axios instance — single source of truth for API base URL
import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

// --- Response interceptor: unwrap { data: ... } envelope ---
client.interceptors.response.use(
  (response) => response.data?.data ?? response.data,
  (error) => {
    const msg = error.response?.data?.error ?? error.message ?? 'Неизвестная ошибка'
    return Promise.reject(new Error(msg))
  },
)

export default client
