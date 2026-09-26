import React, { useState } from 'react'
import type { WebSocketStatus } from '../../types/cocina'
import {
  ChefHat,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  RefreshCw,
  LogOut,
  Radio,
  Flame,
  Clock,
  AlertTriangle,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { playNewOrderChime } from '../../utils/audio'

interface KdsHeaderProps {
  wsStatus: WebSocketStatus
  totalTickets: number
  totalPendientes: number
  totalPreparando: number
  totalDemorados: number
  filtroCanal: string
  onSelectFiltroCanal: (filtro: string) => void
  conteoCanales: {
    todas: number
    mesas: number
    mostrador: number
    domicilio_didi: number
  }
  onRefresh: () => void
  isRefreshing: boolean
  isSoundMuted: boolean
  onToggleSound: () => void
}

export const KdsHeader: React.FC<KdsHeaderProps> = ({
  wsStatus,
  totalTickets,
  totalPendientes,
  totalPreparando,
  totalDemorados,
  filtroCanal,
  onSelectFiltroCanal,
  conteoCanales,
  onRefresh,
  isRefreshing,
  isSoundMuted,
  onToggleSound,
}) => {
  const { logout } = useAuth()
  const [isFullscreen, setIsFullscreen] = useState(false)

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {})
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {})
    }
  }

  const handleTestSound = () => {
    playNewOrderChime()
  }

  return (
    <header className="bg-slate-900 border-b border-slate-800 px-4 py-3 sticky top-0 z-30 shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Marca y Estado WebSocket */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/50 flex items-center justify-center text-amber-400 shrink-0">
            <ChefHat className="w-6 h-6" />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-black text-white tracking-wide uppercase">
                Mr. Burger <span className="text-amber-400">KDS</span>
              </h1>

              {/* Estado WebSocket en Vivo */}
              <div
                className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-black tracking-wide uppercase ${
                  wsStatus === 'conectado'
                    ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/50'
                    : wsStatus === 'reconectando'
                    ? 'bg-amber-950 text-amber-400 border border-amber-500/50 animate-pulse'
                    : 'bg-rose-950 text-rose-400 border border-rose-500/50'
                }`}
                title={
                  wsStatus === 'conectado'
                    ? 'Conexión WebSocket activa en tiempo real'
                    : 'Intentando reconectar con el servidor...'
                }
              >
                <Radio className={`w-3 h-3 ${wsStatus === 'conectado' ? 'animate-pulse text-emerald-400' : ''}`} />
                <span>
                  {wsStatus === 'conectado'
                    ? 'EN VIVO'
                    : wsStatus === 'reconectando'
                    ? 'RECONECTANDO'
                    : 'OFFLINE'}
                </span>
              </div>
            </div>

            <p className="text-[11px] text-slate-400 font-medium hidden sm:block">
              Pantalla de Producción en Cocina • Sin precios ni dinero
            </p>
          </div>
        </div>

        {/* Métricas / Contadores rápidos de Cocina */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700 text-xs font-bold text-slate-200">
            <span className="w-2 h-2 rounded-full bg-amber-400"></span>
            <span>{totalTickets} comanda{totalTickets !== 1 ? 's' : ''}</span>
          </div>

          {totalPendientes > 0 && (
            <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-950/70 border border-amber-800/60 text-xs font-bold text-amber-300">
              <Clock className="w-3.5 h-3.5" />
              <span>{totalPendientes} pendientes</span>
            </div>
          )}

          {totalPreparando > 0 && (
            <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-sky-950/70 border border-sky-800/60 text-xs font-bold text-sky-300">
              <Flame className="w-3.5 h-3.5 text-orange-400" />
              <span>{totalPreparando} en fuego</span>
            </div>
          )}

          {totalDemorados > 0 && (
            <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-950/80 border border-rose-700 text-xs font-black text-rose-300 animate-pulse">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>{totalDemorados} críticas</span>
            </div>
          )}
        </div>

        {/* Botones de Control (Sonido, Pantalla Completa, Refresco, Salir) */}
        <div className="flex items-center gap-2">
          {/* Botón de Sonido con Prueba */}
          <div className="flex items-center rounded-lg bg-slate-800 border border-slate-700 p-0.5">
            <button
              onClick={onToggleSound}
              className={`p-1.5 rounded-md transition cursor-pointer ${
                isSoundMuted
                  ? 'text-rose-400 hover:bg-slate-700'
                  : 'text-amber-400 hover:bg-slate-700'
              }`}
              title={isSoundMuted ? 'Activar timbre de cocina' : 'Silenciar timbre de cocina'}
            >
              {isSoundMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </button>
            {!isSoundMuted && (
              <button
                onClick={handleTestSound}
                className="px-2 py-1 text-[10px] font-bold text-slate-300 hover:text-white hover:bg-slate-700 rounded transition cursor-pointer"
                title="Probar sonido de comanda"
              >
                Campana
              </button>
            )}
          </div>

          {/* Pantalla Completa */}
          <button
            onClick={toggleFullscreen}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white transition cursor-pointer"
            title={isFullscreen ? 'Salir de pantalla completa' : 'Pantalla completa para tablet/monitor'}
          >
            {isFullscreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
          </button>

          {/* Botón Refrescar */}
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white transition cursor-pointer disabled:opacity-50"
            title="Refrescar comanderas manualmente"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-amber-400' : ''}`} />
          </button>

          {/* Salir */}
          <button
            onClick={logout}
            className="p-2 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 border border-rose-800/40 text-rose-400 hover:text-rose-300 transition cursor-pointer"
            title="Cerrar sesión"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Barra de Filtro de Canales */}
      <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
        <button
          onClick={() => onSelectFiltroCanal('TODAS')}
          className={`px-3 py-1 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
            filtroCanal === 'TODAS'
              ? 'bg-amber-500 text-slate-950 shadow'
              : 'bg-slate-800/60 text-slate-400 hover:text-slate-200'
          }`}
        >
          Todas ({conteoCanales.todas})
        </button>

        <button
          onClick={() => onSelectFiltroCanal('MESA')}
          className={`px-3 py-1 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
            filtroCanal === 'MESA'
              ? 'bg-indigo-600 text-white shadow'
              : 'bg-slate-800/60 text-slate-400 hover:text-slate-200'
          }`}
        >
          Mesas ({conteoCanales.mesas})
        </button>

        <button
          onClick={() => onSelectFiltroCanal('MOSTRADOR')}
          className={`px-3 py-1 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
            filtroCanal === 'MOSTRADOR'
              ? 'bg-sky-600 text-white shadow'
              : 'bg-slate-800/60 text-slate-400 hover:text-slate-200'
          }`}
        >
          Mostrador ({conteoCanales.mostrador})
        </button>

        <button
          onClick={() => onSelectFiltroCanal('DOMICILIO_DIDI')}
          className={`px-3 py-1 rounded-lg text-xs font-bold transition whitespace-nowrap cursor-pointer ${
            filtroCanal === 'DOMICILIO_DIDI'
              ? 'bg-purple-600 text-white shadow'
              : 'bg-slate-800/60 text-slate-400 hover:text-slate-200'
          }`}
        >
          Domicilio & DiDi ({conteoCanales.domicilio_didi})
        </button>
      </div>
    </header>
  )
}
