import axios from 'axios'

export const getServerIp = (): string => {
  return localStorage.getItem('pos_server_ip') || ''
}

export const setServerIp = (ip: string): void => {
  const clean = ip.trim().replace(/\/$/, '')
  if (clean) {
    localStorage.setItem('pos_server_ip', clean)
  } else {
    localStorage.removeItem('pos_server_ip')
  }
}

export const getApiBaseUrl = (): string => {
  const customIp = getServerIp()
  if (customIp) {
    if (customIp.startsWith('http://') || customIp.startsWith('https://')) {
      return `${customIp}/api`
    }
    const hostWithPort = customIp.includes(':') ? customIp : `${customIp}:8000`
    return `http://${hostWithPort}/api`
  }
  return import.meta.env.VITE_API_URL || '/api'
}

export const api = axios.create({
  baseURL: getApiBaseUrl(),
})

// Interceptor dinámico para actualizar baseURL si cambia la configuración
api.interceptors.request.use((config) => {
  config.baseURL = getApiBaseUrl()
  const token = localStorage.getItem('pos_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor para redirección si 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Si la ruta no es login y token es inválido/expirado, limpiar sesión
      if (!window.location.pathname.includes('/login')) {
        localStorage.removeItem('pos_token')
        localStorage.removeItem('pos_user')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
