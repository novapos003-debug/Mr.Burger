import React, { useState, useEffect, useCallback } from 'react'
import type { Ticket } from '../types/cocina'
import {
  getColaCocina,
  aceptarDetalle,
  marcarListo,
  aceptarTicket,
  marcarTicketListo,
} from '../api/cocina'
import { useCocinaWebSocket } from '../hooks/useCocinaWebSocket'
import { KdsHeader } from '../components/cocina/KdsHeader'
import { TicketCard } from '../components/cocina/TicketCard'
import {
  isSoundMuted,
  setSoundMuted,
  playNewOrderChime,
} from '../utils/audio'
import { ChefHat, AlertCircle, Loader2 } from 'lucide-react'

export const Cocina: React.FC = () => {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [filtroCanal, setFiltroCanal] = useState<string>('TODAS')
  const [soundMuted, setSoundMutedState] = useState<boolean>(isSoundMuted())

  // Cargar cola de cocina desde el backend
  const fetchCola = useCallback(async (showLoader = false) => {
    try {
      if (showLoader) setIsRefreshing(true)
      const data = await getColaCocina()
      setTickets(data)
      setError(null)
    } catch (err: any) {
      console.error('Error cargando cola de cocina:', err)
      if (err.response?.status === 403) {
        setError('Tu usuario actual no tiene permiso de Cocina. Cierra sesión e ingresa con el usuario "cocina".')
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        setError('Error de conexión con el servidor local. Abre http://localhost:5173 en tu PC o verifica la IP.')
      } else {
        setError(err.response?.data?.detail || 'No se pudo conectar con el servidor de cocina')
      }
    } finally {
      setLoading(false)
      setIsRefreshing(false)
    }
  }, [])

  // Inicialización
  useEffect(() => {
    fetchCola(false)
  }, [fetchCola])

  // WebSocket en tiempo real
  const { status: wsStatus } = useCocinaWebSocket({
    onNewOrder: () => {
      // Suena la campana de cocina y recarga los tickets en vivo
      playNewOrderChime()
      fetchCola(false)
    },
    onOrderUpdate: () => {
      // Recarga de estados (aceptado, listo, finalizado)
      fetchCola(false)
    },
  })

  // Alternar sonido de notificaciones
  const handleToggleSound = () => {
    const nuevoEstado = !soundMuted
    setSoundMuted(nuevoEstado)
    setSoundMutedState(nuevoEstado)
  }

  // Acciones en comanda
  const handleAceptarDetalle = async (detalleId: number) => {
    await aceptarDetalle(detalleId)
    await fetchCola(false)
  }

  const handleMarcarListo = async (detalleId: number) => {
    await marcarListo(detalleId)
    await fetchCola(false)
  }

  const handleAceptarTicket = async (ticket: Ticket) => {
    await aceptarTicket(ticket)
    await fetchCola(false)
  }

  const handleMarcarTicketListo = async (ticket: Ticket) => {
    await marcarTicketListo(ticket)
    await fetchCola(false)
  }

  // Cálculos de métricas para la barra de estado
  let totalPendientes = 0
  let totalPreparando = 0
  let totalDemorados = 0

  let countMesas = 0
  let countMostrador = 0
  let countDelivery = 0

  for (const t of tickets) {
    if (t.canal === 'MESA') countMesas++
    else if (t.canal === 'MOSTRADOR') countMostrador++
    else if (t.canal === 'DOMICILIO' || t.canal === 'DIDI') countDelivery++

    const minutos = Math.floor(t.segundos_transcurridos / 60)
    if (minutos >= 25 || t.tiempo_excedido) {
      totalDemorados++
    }

    for (const r of t.rondas) {
      for (const d of r.detalles) {
        if (d.estado === 'ENVIADO') totalPendientes++
        else if (d.estado === 'PREPARANDO') totalPreparando++
      }
    }
  }

  // Filtrado de tickets según tab seleccionado
  const ticketsFiltrados = tickets.filter((t) => {
    if (filtroCanal === 'TODAS') return true
    if (filtroCanal === 'MESA') return t.canal === 'MESA'
    if (filtroCanal === 'MOSTRADOR') return t.canal === 'MOSTRADOR'
    if (filtroCanal === 'DOMICILIO_DIDI') return t.canal === 'DOMICILIO' || t.canal === 'DIDI'
    return true
  })

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col select-none">
      {/* Cabecera KDS con WebSocket y Controles */}
      <KdsHeader
        wsStatus={wsStatus}
        totalTickets={tickets.length}
        totalPendientes={totalPendientes}
        totalPreparando={totalPreparando}
        totalDemorados={totalDemorados}
        filtroCanal={filtroCanal}
        onSelectFiltroCanal={setFiltroCanal}
        conteoCanales={{
          todas: tickets.length,
          mesas: countMesas,
          mostrador: countMostrador,
          domicilio_didi: countDelivery,
        }}
        onRefresh={() => fetchCola(true)}
        isRefreshing={isRefreshing}
        isSoundMuted={soundMuted}
        onToggleSound={handleToggleSound}
      />

      {/* Área principal del KDS */}
      <main className="flex-1 p-4 flex flex-col">
        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20">
            <Loader2 className="w-10 h-10 text-amber-500 animate-spin mb-3" />
            <p className="text-slate-400 font-bold text-sm">
              Conectando con la cocina en vivo...
            </p>
          </div>
        ) : error ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20 text-center">
            <AlertCircle className="w-12 h-12 text-rose-500 mb-3" />
            <h2 className="text-lg font-bold text-white mb-1">Error de Comunicación</h2>
            <p className="text-sm text-slate-400 max-w-md mb-4">{error}</p>
            <button
              onClick={() => fetchCola(true)}
              className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-sm shadow cursor-pointer"
            >
              Reintentar Conexión
            </button>
          </div>
        ) : ticketsFiltrados.length === 0 ? (
          /* Estado Vacío: Sin pedidos pendientes */
          <div className="flex-1 flex flex-col items-center justify-center py-24 text-center px-4">
            <div className="w-20 h-20 rounded-3xl bg-slate-900 border border-slate-800 flex items-center justify-center text-emerald-400 mb-5 shadow-2xl">
              <ChefHat className="w-10 h-10 text-amber-400" />
            </div>
            <h2 className="text-2xl font-black text-white tracking-wide mb-2">
              ¡Cocina al Día! 👨‍🍳
            </h2>
            <p className="text-slate-400 text-sm max-w-md mb-6 leading-relaxed">
              No hay comandas activas{' '}
              {filtroCanal !== 'TODAS' ? `en el filtro ${filtroCanal}` : 'en la cola de preparación'}.
              Los nuevos pedidos ingresados por los meseros o en caja aparecerán aquí al instante con aviso sonoro.
            </p>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Escuchando canal WebSocket en tiempo real
            </div>
          </div>
        ) : (
          /* Cuadrícula / Tablero Kanban de Comandas */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-4 items-start">
            {ticketsFiltrados.map((ticket) => (
              <TicketCard
                key={ticket.pedido_id}
                ticket={ticket}
                onAceptarDetalle={handleAceptarDetalle}
                onMarcarListo={handleMarcarListo}
                onAceptarTicket={handleAceptarTicket}
                onMarcarTicketListo={handleMarcarTicketListo}
              />
            ))}
          </div>
        )}
      </main>

      {/* Barra de estado inferior */}
      <footer className="bg-slate-950 border-t border-slate-900 px-4 py-2 flex items-center justify-between text-[11px] text-slate-500">
        <div className="flex items-center gap-2">
          <span>Mr. Burger Fast-Food POS</span>
          <span>•</span>
          <span className="text-slate-400">Módulo de Cocina KDS v1.0</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-emerald-500 font-semibold">🔒 Regla estricta: Precios y dinero ocultos</span>
        </div>
      </footer>
    </div>
  )
}
