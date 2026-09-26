import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { checkHealthApi } from '../api/auth'
import {
  UtensilsCrossed,
  Shield,
  Smartphone,
  ChefHat,
  Receipt,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Server,
  Lock,
  User,
  Settings,
} from 'lucide-react'
import { ServerConfigModal } from '../components/common/ServerConfigModal'

export const Login: React.FC = () => {
  const { login, isAuthenticated, user, getRedirectPath } = useAuth()
  const navigate = useNavigate()

  const [usuario, setUsuario] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null)
  const [showServerModal, setShowServerModal] = useState(false)

  // Si ya está autenticado, redirigir a su vista
  useEffect(() => {
    if (isAuthenticated && user) {
      navigate(getRedirectPath(user.rol), { replace: true })
    }
  }, [isAuthenticated, user, navigate, getRedirectPath])

  // Verificar estado del backend local
  useEffect(() => {
    let mounted = true
    const check = async () => {
      const ok = await checkHealthApi()
      if (mounted) setBackendOnline(ok)
    }
    check()
    const interval = setInterval(check, 8000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  const handleLogin = async (u = usuario, p = password) => {
    setError(null)
    if (!u.trim() || !p.trim()) {
      setError('Por favor ingresa usuario y contraseña')
      return
    }

    setLoading(true)
    try {
      const loggedUser = await login(u, p)
      navigate(getRedirectPath(loggedUser.rol), { replace: true })
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Usuario o contraseña incorrectos')
      } else if (err.response?.status === 403) {
        setError('Este usuario se encuentra inactivo')
      } else {
        setError('No se pudo conectar con el servidor local del restaurante')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleQuickLogin = (u: string, p: string) => {
    setUsuario(u)
    setPassword(p)
    handleLogin(u, p)
  }

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4 selection:bg-orange-500 selection:text-white">
      {/* Background radial gradient glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-orange-950/30 via-slate-950 to-slate-950 pointer-events-none" />

      <div className="relative w-full max-w-md z-10">
        {/* Cabecera del Restaurante */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-orange-600 to-amber-500 text-white shadow-xl shadow-orange-600/30 mb-3 transform hover:scale-105 transition">
            <UtensilsCrossed className="w-9 h-9" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white uppercase">
            Mr. Burger POS
          </h1>
          <p className="text-slate-400 text-xs sm:text-sm mt-1">
            Sistema de Operación en Vivo • Cali
          </p>

          {/* Indicador de Cerebro Local */}
          <div className="inline-flex items-center gap-1.5 mt-3 px-3 py-1 rounded-full text-xs font-semibold bg-slate-900 border border-slate-800">
            <Server className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-300">Cerebro Local:</span>
            {backendOnline === null ? (
              <span className="text-slate-500">Verificando...</span>
            ) : backendOnline ? (
              <span className="flex items-center gap-1 text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                En línea (LAN)
              </span>
            ) : (
              <span className="flex items-center gap-1 text-red-400">
                <span className="w-2 h-2 rounded-full bg-red-500"></span>
                Desconectado
              </span>
            )}
            <button
              type="button"
              onClick={() => setShowServerModal(true)}
              title="Configurar IP del Servidor"
              className="ml-1 text-slate-400 hover:text-white p-0.5 rounded cursor-pointer transition"
            >
              <Settings className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Tarjeta de Formulario de Login */}
        <div className="bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl shadow-black/50">
          <h2 className="text-base font-bold text-slate-200 mb-4 flex items-center gap-2">
            <Lock className="w-4 h-4 text-orange-500" />
            Iniciar Sesión
          </h2>

          {error && (
            <div className="mb-4 p-3 bg-red-950/80 border border-red-800 text-red-200 rounded-xl text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleLogin()
            }}
            className="space-y-4"
          >
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
                Usuario
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={usuario}
                  onChange={(e) => setUsuario(e.target.value)}
                  placeholder="ej. mesero, cocina, caja, admin"
                  disabled={loading}
                  className="w-full pl-9 pr-3 py-2.5 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
                Contraseña
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={loading}
                  className="w-full pl-9 pr-10 py-2.5 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-500 hover:text-slate-300"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 active:scale-[0.98] text-white font-bold rounded-xl shadow-lg shadow-orange-600/30 transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 text-sm"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Entrando...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Acceder al Sistema</span>
                </>
              )}
            </button>
          </form>

          {/* Separador */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-800"></div>
            </div>
            <div className="relative flex justify-center text-[11px] uppercase tracking-wider">
              <span className="bg-slate-900 px-3 text-slate-500 font-semibold">
                Acceso Rápido por Rol (Demostración)
              </span>
            </div>
          </div>

          {/* Botones de Acceso Rápido para Pruebas y Presentación */}
          <div className="grid grid-cols-2 gap-2.5">
            <button
              type="button"
              onClick={() => handleQuickLogin('mesero', 'mesero123')}
              disabled={loading}
              className="flex items-center gap-2 p-2.5 rounded-xl bg-orange-950/40 hover:bg-orange-950/80 border border-orange-800/60 text-orange-200 transition text-left cursor-pointer group"
            >
              <div className="w-7 h-7 rounded-lg bg-orange-600/30 flex items-center justify-center group-hover:scale-110 transition shrink-0">
                <Smartphone className="w-4 h-4 text-orange-400" />
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-bold leading-tight truncate">Mesero</p>
                <p className="text-[10px] text-orange-400/80 truncate">Móvil / Tablet</p>
              </div>
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin('cocina', 'cocina123')}
              disabled={loading}
              className="flex items-center gap-2 p-2.5 rounded-xl bg-amber-950/40 hover:bg-amber-950/80 border border-amber-800/60 text-amber-200 transition text-left cursor-pointer group"
            >
              <div className="w-7 h-7 rounded-lg bg-amber-600/30 flex items-center justify-center group-hover:scale-110 transition shrink-0">
                <ChefHat className="w-4 h-4 text-amber-400" />
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-bold leading-tight truncate">Cocina KDS</p>
                <p className="text-[10px] text-amber-400/80 truncate">Pantalla Tickets</p>
              </div>
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin('caja', 'caja123')}
              disabled={loading}
              className="flex items-center gap-2 p-2.5 rounded-xl bg-emerald-950/40 hover:bg-emerald-950/80 border border-emerald-800/60 text-emerald-200 transition text-left cursor-pointer group"
            >
              <div className="w-7 h-7 rounded-lg bg-emerald-600/30 flex items-center justify-center group-hover:scale-110 transition shrink-0">
                <Receipt className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-bold leading-tight truncate">Caja / POS</p>
                <p className="text-[10px] text-emerald-400/80 truncate">Cobros y Arqueo</p>
              </div>
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin('admin', 'admin123')}
              disabled={loading}
              className="flex items-center gap-2 p-2.5 rounded-xl bg-purple-950/40 hover:bg-purple-950/80 border border-purple-800/60 text-purple-200 transition text-left cursor-pointer group"
            >
              <div className="w-7 h-7 rounded-lg bg-purple-600/30 flex items-center justify-center group-hover:scale-110 transition shrink-0">
                <Shield className="w-4 h-4 text-purple-400" />
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-bold leading-tight truncate">Admin / Dueño</p>
                <p className="text-[10px] text-purple-400/80 truncate">Dashboard y Control</p>
              </div>
            </button>
          </div>
        </div>

        {/* Pie de página con versión */}
        <p className="text-center text-[11px] text-slate-500 mt-4">
          PWA Offline Ready • WebSockets Instantáneos • v1.0.0
        </p>
      </div>

      <ServerConfigModal
        isOpen={showServerModal}
        onClose={() => setShowServerModal(false)}
        onSave={async () => {
          const ok = await checkHealthApi()
          setBackendOnline(ok)
        }}
      />
    </div>
  )
}
