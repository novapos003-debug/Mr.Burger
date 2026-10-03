import React, { createContext, useContext, useState, useEffect } from 'react'
import type { Usuario, UserRole } from '../types/auth'
import { loginApi, getMeApi } from '../api/auth'

import type { TurnoLaboral } from '../types/asistencia'
import { registrarEntradaApi, registrarSalidaApi, obtenerMiTurnoApi } from '../api/asistencia'
import api, { getWsBaseUrl } from '../api/client'

interface AuthContextType {
  user: Usuario | null
  token: string | null
  loading: boolean
  turno: TurnoLaboral | null
  login: (usuario: string, password: string) => Promise<Usuario>
  logout: () => void
  cerrarTurnoYSalir: () => Promise<void>
  isAuthenticated: boolean
  hasRole: (roles: UserRole[]) => boolean
  getRedirectPath: (role: UserRole) => string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const getRedirectPath = (role: UserRole): string => {
  switch (role) {
    case 'admin':
      return '/admin'
    case 'cajero':
      return '/caja'
    case 'mesero':
      return '/mesero'
    case 'cocina':
      return '/cocina'
    default:
      return '/login'
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<Usuario | null>(() => {
    const saved = localStorage.getItem('pos_user')
    return saved ? JSON.parse(saved) : null
  })
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('pos_token'))
  const [loading, setLoading] = useState<boolean>(true)
  const [turno, setTurno] = useState<TurnoLaboral | null>(null)

  // Cargar estado inicial y turno
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('pos_token')
      if (storedToken) {
        try {
          const me = await getMeApi()
          if (localStorage.getItem('pos_token') === storedToken) {
            setUser(me)
            localStorage.setItem('pos_user', JSON.stringify(me))
            
            if (me.rol !== 'admin') {
              const miTurno = await obtenerMiTurnoApi()
              if (localStorage.getItem('pos_token') === storedToken) {
                setTurno(miTurno)
              }
            }
          }
        } catch (err: any) {
          // Solo limpiar si el token no fue reemplazado por un nuevo login
          if (localStorage.getItem('pos_token') === storedToken) {
            if (err.response?.status === 401) {
              localStorage.removeItem('pos_token')
              localStorage.removeItem('pos_user')
              setToken(null)
              setUser(null)
              setTurno(null)
            } else {
              const savedUser = localStorage.getItem('pos_user')
              if (savedUser) {
                try { setUser(JSON.parse(savedUser)) } catch {}
              }
            }
          }
        }
      }
      setLoading(false)
    }

    initAuth()
  }, [])

  // Listener global de WebSocket para el evento de cierre de caja
  useEffect(() => {
    if (!token || !user || user.rol === 'admin') return

    let ws: WebSocket
    let pingInterval: number

    const connect = () => {
      const baseWs = getWsBaseUrl()
      const separator = baseWs.includes('?') ? '&' : '?'
      const wsUrl = `${baseWs}${separator}token=${encodeURIComponent(token)}`
      
      try {
        ws = new WebSocket(wsUrl)
        ws.onopen = () => {
          pingInterval = window.setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) ws.send('ping')
          }, 15000)
        }
        ws.onmessage = (event) => {
          if (event.data === 'pong') return
          try {
            const payload = JSON.parse(event.data)
            if (payload.evento === 'cierre_caja_general') {
              alert(payload.data?.mensaje || 'Día laboral finalizado. Se ha cerrado la caja.')
              logout()
            } else if (payload.evento === 'cierre_turno_forzado' && payload.data?.usuario_id === user.id) {
              alert(payload.data?.mensaje || 'Tu turno de trabajo ha sido cerrado por el administrador.')
              logout()
            }
          } catch (e) {}
        }
        ws.onclose = (e) => {
          if (pingInterval) clearInterval(pingInterval)
          if (e.code !== 1008) setTimeout(connect, 5000)
        }
      } catch (err) {}
    }

    connect()

    // Sondeo de seguridad: si el turno se cerró por admin o caja (o el WS falló)
    const verificarTurno = async () => {
      try {
        const miTurno = await obtenerMiTurnoApi()
        if (!miTurno) {
          alert('Tu turno de trabajo ha sido cerrado. Tu sesión ha finalizado.')
          logout()
        } else {
          setTurno(miTurno)
        }
      } catch (err: any) {
        if (err.response?.status === 401) {
          logout()
        }
      }
    }

    // Verificación menos agresiva para no inundar el servidor (de 8s pasó a 60s)
    const timerTurno = setInterval(verificarTurno, 60000)
    const handleVisibility = () => {
      if (document.visibilityState === 'visible') {
        verificarTurno()
      }
    }
    document.addEventListener('visibilitychange', handleVisibility)

    return () => {
      if (pingInterval) clearInterval(pingInterval)
      if (ws) ws.close()
      clearInterval(timerTurno)
      document.removeEventListener('visibilitychange', handleVisibility)
    }
  }, [token, user])

  const login = async (usuario: string, password: string): Promise<Usuario> => {
    const data = await loginApi(usuario, password)
    localStorage.setItem('pos_token', data.access_token)
    setToken(data.access_token)
    api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`

    const me = await getMeApi()
    setUser(me)
    localStorage.setItem('pos_user', JSON.stringify(me))

    // Al iniciar sesión, registramos o traemos el turno activo automáticamente
    if (me.rol !== 'admin') {
      try {
        const turnoNuevo = await registrarEntradaApi()
        setTurno(turnoNuevo)
      } catch (err) {
        console.error('Error al registrar turno:', err)
      }
    }

    return me
  }

  const logout = () => {
    localStorage.removeItem('pos_token')
    localStorage.removeItem('pos_user')
    setToken(null)
    setUser(null)
    setTurno(null)
    window.location.href = '/login'
  }

  const cerrarTurnoYSalir = async () => {
    try {
      await registrarSalidaApi()
    } catch (err) {
      console.error('Error cerrando turno:', err)
    } finally {
      logout()
    }
  }

  const hasRole = (roles: UserRole[]): boolean => {
    if (!user) return false
    return roles.includes(user.rol)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        turno,
        login,
        logout,
        cerrarTurnoYSalir,
        isAuthenticated: !!user && !!token,
        hasRole,
        getRedirectPath,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth debe ser usado dentro de un AuthProvider')
  }
  return context
}
