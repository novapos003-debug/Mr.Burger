import React, { useState, useEffect } from 'react'
import type {
  Ticket,
  TicketDetalle,
  VariacionSnapshot,
} from '../../types/cocina'
import {
  Clock,
  Flame,
  CheckCircle2,
  AlertTriangle,
  MapPin,
  Phone,
  User,
  Zap,
  Layers,
  UtensilsCrossed,
  Bike,
  Store,
  ShoppingBag,
  Loader2,
} from 'lucide-react'

interface TicketCardProps {
  ticket: Ticket
  onAceptarDetalle: (detalleId: number) => Promise<void>
  onMarcarListo: (detalleId: number) => Promise<void>
  onAceptarTicket: (ticket: Ticket) => Promise<void>
  onMarcarTicketListo: (ticket: Ticket) => Promise<void>
}

export const TicketCard: React.FC<TicketCardProps> = ({
  ticket,
  onAceptarDetalle,
  onMarcarListo,
  onAceptarTicket,
  onMarcarTicketListo,
}) => {
  const [segundos, setSegundos] = useState(ticket.segundos_transcurridos)
  const [loadingAction, setLoadingAction] = useState<string | null>(null)

  // Temporizador en tiempo real: avanza segundo a segundo en la pantalla
  useEffect(() => {
    setSegundos(ticket.segundos_transcurridos)
    const interval = setInterval(() => {
      setSegundos((prev) => prev + 1)
    }, 1000)
    return () => clearInterval(interval)
  }, [ticket.segundos_transcurridos])

  const minutos = Math.floor(segundos / 60)
  const segRestantes = segundos % 60
  const tiempoStr = `${minutos.toString().padStart(2, '0')}:${segRestantes.toString().padStart(2, '0')}`

  // Alerta de tiempo (regla de SLA: 28 min de tolerancia)
  const esAlertaCritica = minutos >= 25 || ticket.tiempo_excedido
  const esAlertaMedia = minutos >= 15 && minutos < 25

  // Conteo de estados en los detalles
  let countEnviados = 0
  let countPreparando = 0
  let countListos = 0

  for (const r of ticket.rondas) {
    for (const d of r.detalles) {
      if (d.estado === 'ENVIADO') countEnviados++
      else if (d.estado === 'PREPARANDO') countPreparando++
      else if (d.estado === 'LISTO') countListos++
    }
  }

  const handleAction = async (actionKey: string, fn: () => Promise<void>) => {
    try {
      setLoadingAction(actionKey)
      await fn()
    } catch (err: any) {
      console.error('Error ejecutando acción de cocina:', err)
      alert(err.response?.data?.detail || 'Error al procesar comanda en cocina')
    } finally {
      setLoadingAction(null)
    }
  }

  // Renderizador de variaciones y adiciones
  const renderVariaciones = (v?: VariacionSnapshot | null) => {
    if (!v) return null

    const esPreparado = v.es_preparado || v.preparado_id

    return (
      <div className="mt-1.5 space-y-1">
        {esPreparado && (
          <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-purple-900/60 border border-purple-500 text-purple-200 text-[11px] font-bold tracking-wide animate-pulse">
            <Zap className="w-3 h-3 text-yellow-300" />
            REUTILIZAR PREPARADO EXISTENTE (Cancelado previo)
          </div>
        )}

        {/* Modificaciones (sin cebolla, carne asada, etc.) */}
        {v.modificaciones && v.modificaciones.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {v.modificaciones.map((mod, idx) => (
              <span
                key={idx}
                className="inline-block px-1.5 py-0.5 rounded text-[11px] font-semibold bg-rose-950/70 border border-rose-800/60 text-rose-300"
              >
                {mod.startsWith('Sin') ? '❌ ' : '📝 '}
                {mod}
              </span>
            ))}
          </div>
        )}

        {/* Adiciones extras */}
        {v.adiciones && v.adiciones.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {v.adiciones.map((adic, idx) => (
              <span
                key={idx}
                className="inline-block px-1.5 py-0.5 rounded text-[11px] font-bold bg-amber-950/70 border border-amber-700/60 text-amber-300"
              >
                ➕ {adic.nombre}
              </span>
            ))}
          </div>
        )}

        {/* Notas personalizadas */}
        {v.notas && (
          <p className="text-[11px] italic text-slate-300 bg-slate-800/60 rounded px-2 py-0.5 border border-slate-700/50">
            "{v.notas}"
          </p>
        )}
      </div>
    )
  }

  // Canal icono y color
  const getCanalBadge = () => {
    switch (ticket.canal) {
      case 'MESA':
        return (
          <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg font-black text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
            <UtensilsCrossed className="w-3.5 h-3.5" />
            MESA {ticket.mesa_numero}
          </span>
        )
      case 'MOSTRADOR':
        return (
          <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg font-black text-xs bg-sky-500/20 text-sky-300 border border-sky-500/40">
            <Store className="w-3.5 h-3.5" />
            MOSTRADOR
          </span>
        )
      case 'DOMICILIO':
        return (
          <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg font-black text-xs bg-purple-500/20 text-purple-300 border border-purple-500/40">
            <Bike className="w-3.5 h-3.5" />
            DOMICILIO
          </span>
        )
      case 'DIDI':
        return (
          <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg font-black text-xs bg-orange-500/20 text-orange-300 border border-orange-500/40">
            <ShoppingBag className="w-3.5 h-3.5" />
            DIDI FOOD
          </span>
        )
      default:
        return null
    }
  }

  return (
    <div
      className={`flex flex-col bg-slate-900 rounded-2xl border transition-all duration-300 overflow-hidden shadow-2xl ${
        esAlertaCritica
          ? 'border-rose-500/80 ring-2 ring-rose-500/40 shadow-rose-950/40'
          : esAlertaMedia
          ? 'border-amber-500/70 shadow-amber-950/30'
          : 'border-slate-800 hover:border-slate-700'
      }`}
    >
      {/* Cabecera del Ticket */}
      <div
        className={`px-4 py-3 border-b flex items-center justify-between ${
          esAlertaCritica
            ? 'bg-rose-950/50 border-rose-800/60'
            : esAlertaMedia
            ? 'bg-amber-950/40 border-amber-800/50'
            : 'bg-slate-800/60 border-slate-800'
        }`}
      >
        <div className="flex items-center gap-2">
          <span className="text-xl font-black text-white tracking-wider">
            #{ticket.consecutivo}
          </span>
          {getCanalBadge()}
        </div>

        {/* Cronómetro Monospace con Alerta Visual */}
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border font-mono font-bold text-sm tracking-widest ${
            esAlertaCritica
              ? 'bg-rose-600/30 text-rose-300 border-rose-500 animate-pulse'
              : esAlertaMedia
              ? 'bg-amber-600/30 text-amber-300 border-amber-500'
              : 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40'
          }`}
          title={`Temporizador Cocina: SLA ${ticket.minutos_temporizador} min`}
        >
          <Clock className="w-4 h-4" />
          <span>{tiempoStr}</span>
        </div>
      </div>

      {/* Alerta de tiempo excedido si supera los 28 minutos */}
      {esAlertaCritica && (
        <div className="bg-rose-600 text-white px-3 py-1 flex items-center justify-center gap-1.5 text-xs font-black uppercase tracking-wider animate-pulse">
          <AlertTriangle className="w-3.5 h-3.5" />
          Tiempo Excedido ({minutos} min en espera)
        </div>
      )}

      {/* Datos del Cliente / Domicilio si existen */}
      {(ticket.cliente || ticket.telefono || ticket.direccion) && (
        <div className="px-4 py-2 bg-slate-950/60 border-b border-slate-800/80 text-xs text-slate-300 space-y-1">
          <div className="flex items-center gap-2">
            {ticket.cliente && (
              <span className="flex items-center gap-1 font-semibold text-slate-200">
                <User className="w-3 h-3 text-slate-400" />
                {ticket.cliente}
              </span>
            )}
            {ticket.telefono && (
              <span className="flex items-center gap-1 text-slate-400">
                <Phone className="w-3 h-3" />
                {ticket.telefono}
              </span>
            )}
          </div>
          {ticket.direccion && (
            <div className="flex items-center gap-1 text-slate-400">
              <MapPin className="w-3 h-3 text-amber-400 shrink-0" />
              <span className="truncate">{ticket.direccion}</span>
            </div>
          )}
        </div>
      )}

      {/* Nota Interna de la Comanda */}
      {ticket.nota_interna && (
        <div className="px-4 py-2 bg-amber-950/30 border-b border-amber-800/40 text-xs text-amber-200 flex items-start gap-1.5 font-medium">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
          <span>
            <strong className="text-amber-300">Nota:</strong> {ticket.nota_interna}
          </span>
        </div>
      )}

      {/* Lista de Rondas y Productos */}
      <div className="flex-1 p-3 space-y-3 overflow-y-auto max-h-[380px]">
        {ticket.rondas.map((ronda) => (
          <div key={ronda.ronda} className="space-y-2">
            {/* Cabecera de Ronda si hay más de 1 */}
            {(ticket.rondas.length > 1 || ronda.ronda > 1) && (
              <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-slate-800/80 text-[11px] font-bold text-slate-300 border border-slate-700/60">
                <Layers className="w-3 h-3 text-amber-400" />
                <span>
                  {ronda.ronda === 1
                    ? 'Ronda 1 • Pedido Inicial'
                    : `Ronda ${ronda.ronda} • ADICIONAL EN MARCHA`}
                </span>
              </div>
            )}

            {/* Detalles de la ronda */}
            <div className="space-y-2">
              {ronda.detalles.map((detalle: TicketDetalle) => {
                const isDetailLoading = loadingAction === `d-${detalle.detalle_id}`
                const isEnviado = detalle.estado === 'ENVIADO'
                const isPreparando = detalle.estado === 'PREPARANDO'
                const isListo = detalle.estado === 'LISTO'

                return (
                  <div
                    key={detalle.detalle_id}
                    className={`p-2.5 rounded-xl border transition-all ${
                      isListo
                        ? 'bg-emerald-950/20 border-emerald-900/40 opacity-70'
                        : isPreparando
                        ? 'bg-sky-950/30 border-sky-800/50'
                        : 'bg-slate-800/40 border-slate-700/50'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2">
                        {/* Cantidad grande y clara */}
                        <span className="w-7 h-7 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center font-black text-amber-400 text-sm shrink-0">
                          {Number(detalle.cantidad)}x
                        </span>

                        <div>
                          <p className="font-bold text-white text-sm leading-tight">
                            {detalle.producto_nombre}
                          </p>

                          {/* Variaciones, modificaciones, adiciones */}
                          {renderVariaciones(detalle.variacion_snapshot)}
                        </div>
                      </div>

                      {/* Estado actual / Botón de Acción individual */}
                      <div className="shrink-0 flex flex-col items-end gap-1">
                        {isEnviado && (
                          <button
                            disabled={!!loadingAction}
                            onClick={() =>
                              handleAction(`d-${detalle.detalle_id}`, () =>
                                onAceptarDetalle(detalle.detalle_id)
                              )
                            }
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-black text-xs bg-amber-600 hover:bg-amber-500 active:scale-95 text-slate-950 shadow-md transition cursor-pointer disabled:opacity-50"
                            title="Aceptar y descontar inventario"
                          >
                            {isDetailLoading ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <Flame className="w-3.5 h-3.5" />
                            )}
                            Preparar
                          </button>
                        )}

                        {isPreparando && (
                          <button
                            disabled={!!loadingAction}
                            onClick={() =>
                              handleAction(`d-${detalle.detalle_id}`, () =>
                                onMarcarListo(detalle.detalle_id)
                              )
                            }
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-black text-xs bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white shadow-md transition cursor-pointer disabled:opacity-50"
                            title="Marcar producto como listo"
                          >
                            {isDetailLoading ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <CheckCircle2 className="w-3.5 h-3.5" />
                            )}
                            Listo
                          </button>
                        )}

                        {isListo && (
                          <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-900/40 text-emerald-400 border border-emerald-700/50">
                            <CheckCircle2 className="w-3 h-3" />
                            Listo
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Acciones Masivas por Comanda */}
      <div className="p-3 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-400">
          {countEnviados > 0 && (
            <span className="px-1.5 py-0.5 rounded bg-amber-950/60 text-amber-400 border border-amber-800/50">
              {countEnviados} pendiente{countEnviados > 1 ? 's' : ''}
            </span>
          )}
          {countPreparando > 0 && (
            <span className="px-1.5 py-0.5 rounded bg-sky-950/60 text-sky-400 border border-sky-800/50">
              {countPreparando} en fuego
            </span>
          )}
          {countListos > 0 && (
            <span className="px-1.5 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/50">
              {countListos} listo{countListos > 1 ? 's' : ''}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {countEnviados > 0 && (
            <button
              disabled={!!loadingAction}
              onClick={() =>
                handleAction(`ticket-aceptar-${ticket.pedido_id}`, () =>
                  onAceptarTicket(ticket)
                )
              }
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg font-black text-xs bg-amber-500 hover:bg-amber-400 text-slate-950 transition active:scale-95 disabled:opacity-50 cursor-pointer shadow"
              title="Aceptar todos los productos pendientes de este ticket"
            >
              {loadingAction === `ticket-aceptar-${ticket.pedido_id}` ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Flame className="w-3.5 h-3.5" />
              )}
              Todo a Cocina
            </button>
          )}

          {countPreparando > 0 && countEnviados === 0 && (
            <button
              disabled={!!loadingAction}
              onClick={() =>
                handleAction(`ticket-listo-${ticket.pedido_id}`, () =>
                  onMarcarTicketListo(ticket)
                )
              }
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg font-black text-xs bg-emerald-600 hover:bg-emerald-500 text-white transition active:scale-95 disabled:opacity-50 cursor-pointer shadow"
              title="Marcar toda la comanda como lista"
            >
              {loadingAction === `ticket-listo-${ticket.pedido_id}` ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <CheckCircle2 className="w-3.5 h-3.5" />
              )}
              Despachar Todo
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
