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
  // En localhost o 127.0.0.1 (el computador servidor local), usar siempre el proxy local de Vite
  if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    return '/api'
  }
  const customIp = getServerIp()
  if (customIp) {
    const clean = customIp.trim().replace(/\/api$/, '').replace(/\/$/, '')
    if (clean.startsWith('http://') || clean.startsWith('https://')) {
      return `${clean}/api`
    }
    const hostWithPort = clean.includes(':') ? clean : `${clean}:8000`
    return `http://${hostWithPort}/api`
  }
  // Si estamos en la nube (Firebase Hosting), apuntar por defecto a Render
  if (
    typeof window !== 'undefined' &&
    (window.location.hostname.includes('web.app') || window.location.hostname.includes('firebaseapp.com'))
  ) {
    return 'https://mrburger-api.onrender.com/api'
  }
  return import.meta.env.VITE_API_URL || '/api'
}

export const getWsBaseUrl = (): string => {
  if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}/ws/pedidos`
  }
  const customIp = getServerIp()
  if (customIp) {
    const clean = customIp.replace(/^https?:\/\//, '').replace(/\/api$/, '').replace(/\/$/, '')
    const isHttps = customIp.startsWith('https://')
    const protocol = isHttps ? 'wss:' : 'ws:'
    const hostWithPort = clean.includes(':') ? clean : `${clean}:8000`
    return `${protocol}//${hostWithPort}/ws/pedidos`
  }
  if (
    typeof window !== 'undefined' &&
    (window.location.hostname.includes('web.app') || window.location.hostname.includes('firebaseapp.com'))
  ) {
    return 'wss://mrburger-api.onrender.com/ws/pedidos'
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/pedidos`
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
      // Si la petición fallida fue hecha con un token anterior/obsoleto, ignorar el 401 para evitar expulsar una sesión recién iniciada
      const reqAuth = (error.config?.headers?.Authorization || '') as string
      const currentToken = localStorage.getItem('pos_token')
      if (reqAuth && currentToken && !reqAuth.includes(currentToken)) {
        return Promise.reject(error)
      }

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
