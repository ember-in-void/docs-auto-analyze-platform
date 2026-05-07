// ==========================================
// Auth API — Login & Register
// ==========================================
import client from './client'

export async function login(email, password) {
  const data = await client.post('/auth/login', { email, password })
  return data
}

export async function register(email, password, fullName) {
  const data = await client.post('/auth/register', { email, password, full_name: fullName })
  return data
}
