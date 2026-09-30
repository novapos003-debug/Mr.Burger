import React, { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import {
  UtensilsCrossed,
  LogOut,
  Shield,
  Smartphone,
  ChefHat,
  Receipt,
  User,
  Settings,
} from 'lucide-react'
import type { UserRole } from '../types/auth'
import { SyncBadge } from './common/SyncBadge'
import { ServerConfigModal } from './common/ServerConfigModal'

export const Navbar: React.FC<{ title?: string }> = ({ title }) => {
  const { user, logout, cerrarTurnoYSalir, turno } = useAuth()
  const [hora, setHora] = useState<string>('')
  const [showServerModal, setShowServerModal] = useState(false)

  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      setHora(
        now.toLocaleTimeString('es-CO', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: true,
        })
      )
    }
    updateTime()
    const timer = setInterval(updateTime, 1000)
    return () => clearInterval(timer)
  }, [])

  const getRoleBadge = (role: UserRole) => {
    switch (role) {
      case 'admin':
        return {
          icon: <Shield className="w-4 h-4 text-purple-400" />,
          label: 'ADMINISTRADOR',
          bg: 'bg-purple-950/80 border-purple-600 text-purple-200',
        }
      case 'cajero':
        return {
          icon: <Receipt className="w-4 h-4 text-emerald-400" />,
          label: 'CAJA / POS',
          bg: 'bg-emerald-950/80 border-emerald-600 text-emerald-200',
        }
      case 'cocina':
        return {
          icon: <ChefHat className="w-4 h-4 text-amber-400" />,
          label: 'COCINA KDS',
          bg: 'bg-amber-950/80 border-amber-600 text-amber-200',
        }
      case 'mesero':
        return {
          icon: <Smartphone className="w-4 h-4 text-orange-400" />,
          label: 'MESERO MÓVIL',
          bg: 'bg-orange-950/80 border-orange-600 text-orange-200',
        }
    }
  }

  const roleInfo = user ? getRoleBadge(user.rol) : null

  return (
    <header className="bg-slate-900/90 backdrop-blur border-b border-slate-800 px-4 py-2.5 flex items-center justify-between select-none z-30 sticky top-0">
      {/* Brand & Section Title */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-orange-600 flex items-center justify-center text-white shadow-lg shadow-orange-600/20">
          <UtensilsCrossed className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-black text-sm tracking-wider uppercase text-white">MR. BURGER</span>
            <SyncBadge />
          </div>
          <p className="text-[11px] text-slate-400 font-medium">
            {title || 'Sistema Rápido Mr. Burger'}
          </p>
        </div>
      </div>

      {/* Reloj y Usuario */}
      <div className="flex items-center gap-3">
        {/* Reloj en vivo */}
        <div className="hidden sm:flex flex-col items-end">
          <span className="text-xs font-mono font-semibold text-slate-300 bg-slate-950 px-2.5 py-1 rounded border border-slate-800">
            {hora || '--:--:--'}
          </span>
        </div>

        {/* Info Usuario */}
        {user && roleInfo && (
          <div className="flex items-center gap-2">
            {turno && (
              <div className="hidden lg:flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-md border bg-slate-950/80 border-slate-700 text-slate-300">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Turno Abierto
              </div>
            )}
            <div className={`hidden md:flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-md border ${roleInfo.bg}`}>
              {roleInfo.icon}
              <span>{roleInfo.label}</span>
            </div>

            <div className="flex items-center gap-2 bg-slate-950 px-2.5 py-1 rounded-md border border-slate-800 text-xs">
              <User className="w-3.5 h-3.5 text-slate-400" />
              <span className="font-medium text-slate-200">{user.nombre}</span>
            </div>

            <button
              onClick={() => setShowServerModal(true)}
              title="Configuración de Servidor"
              className="flex items-center text-slate-400 hover:text-white bg-slate-950 hover:bg-slate-800 border border-slate-800 p-1.5 rounded-md text-xs transition cursor-pointer"
            >
              <Settings className="w-3.5 h-3.5" />
            </button>

            {user.rol !== 'admin' ? (
              <button
                onClick={() => {
                  if (confirm('¿Estás seguro de que deseas cerrar tu turno y salir?')) {
                    cerrarTurnoYSalir()
                  }
                }}
                title="Cerrar turno"
                className="flex items-center gap-1 bg-red-950/60 hover:bg-red-900 border border-red-800/70 text-red-300 hover:text-white px-2.5 py-1 rounded-md text-xs font-medium transition cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Cerrar Turno</span>
              </button>
            ) : (
              <button
                onClick={logout}
                title="Cerrar sesión"
                className="flex items-center gap-1 bg-red-950/60 hover:bg-red-900 border border-red-800/70 text-red-300 hover:text-white px-2.5 py-1 rounded-md text-xs font-medium transition cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Salir</span>
              </button>
            )}
          </div>
        )}
      </div>

      <ServerConfigModal
        isOpen={showServerModal}
        onClose={() => setShowServerModal(false)}
      />
    </header>
  )
}
