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
  // En la propia máquina servidora (localhost / 127.0.0.1), conectar SIEMPRE de forma directa a localhost:8000 (funciona 100% offline)
  if (
    typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ) {
    return 'http://localhost:8000/api'
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

  // En desarrollo con Vite (npm run dev), usar el proxy local de Vite
  if (import.meta.env.DEV) {
    return '/api'
  }

  // En producción LAN, conectar directamente al puerto 8000 del host
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:'
    const hostname = window.location.hostname || 'localhost'
    return `${protocol}//${hostname}:8000/api`
  }

  return import.meta.env.VITE_API_URL || '/api'
}

export const getWsBaseUrl = (): string => {
  if (
    typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ) {
    return 'ws://localhost:8000/ws/pedidos'
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

  // En desarrollo con Vite, el proxy maneja ws://localhost:5173/ws/pedidos
  if (import.meta.env.DEV && typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}/ws/pedidos`
  }

  // En producción (Termux / LAN), conectar directamente al puerto 8000 del servidor
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const hostname = window.location.hostname || 'localhost'
    return `${protocol}//${hostname}:8000/ws/pedidos`
  }

  return 'ws://localhost:8000/ws/pedidos'
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
      const url = (error.config?.url || '') as string
      if (url.includes('/auth/login')) {
        return Promise.reject(error)
      }

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
