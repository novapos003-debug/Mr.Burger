import React, { createContext, useContext, useState, useEffect } from 'react'
import type { Usuario, UserRole } from '../types/auth'
import { loginApi, getMeApi } from '../api/auth'

interface AuthContextType {
  user: Usuario | null
  token: string | null
  loading: boolean
  login: (usuario: string, password: string) => Promise<Usuario>
  logout: () => void
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

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('pos_token')
      if (storedToken) {
        try {
          const me = await getMeApi()
          setUser(me)
          localStorage.setItem('pos_user', JSON.stringify(me))
        } catch (err: any) {
          // Si el servidor responde explícitamente 401, el token expiró o es inválido
          if (err.response?.status === 401) {
            localStorage.removeItem('pos_token')
            localStorage.removeItem('pos_user')
            setToken(null)
            setUser(null)
          } else {
            // Si fue error de red/sin conexión, mantener el usuario guardado para operar offline
            const savedUser = localStorage.getItem('pos_user')
            if (savedUser) {
              try {
                setUser(JSON.parse(savedUser))
              } catch {
                // ignore
              }
            }
          }
        }
      }
      setLoading(false)
    }

    initAuth()
  }, [])

  const login = async (usuario: string, password: string): Promise<Usuario> => {
    const data = await loginApi(usuario, password)
    localStorage.setItem('pos_token', data.access_token)
    setToken(data.access_token)

    const me = await getMeApi()
    setUser(me)
    localStorage.setItem('pos_user', JSON.stringify(me))
    return me
  }

  const logout = () => {
    localStorage.removeItem('pos_token')
    localStorage.removeItem('pos_user')
    setToken(null)
    setUser(null)
    window.location.href = '/login'
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
        login,
        logout,
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
