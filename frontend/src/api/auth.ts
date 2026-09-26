import api from './client'
import type { Usuario } from '../types/auth'

export interface TokenResult {
  access_token: string
  token_type: string
}

export const loginApi = async (username: string, password: string): Promise<TokenResult> => {
  const params = new URLSearchParams()
  params.append('username', username)
  params.append('password', password)

  const response = await api.post<TokenResult>('/auth/login', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
  return response.data
}

export const getMeApi = async (): Promise<Usuario> => {
  const response = await api.get<Usuario>('/auth/me')
  return response.data
}

export const checkHealthApi = async (): Promise<boolean> => {
  try {
    const response = await api.get('/health', { timeout: 3000 })
    return response.status === 200
  } catch {
    return false
  }
}
