import React from 'react'
import type { CartItem, Mesa, Pedido } from '../../types/mesero'
import {
  Send,
  Trash2,
  Plus,
  Minus,
  Utensils,
  Layers,
  Zap,
} from 'lucide-react'

interface Props {
  items: CartItem[]
  mesa: Mesa | null
  pedidoActivo: Pedido | null
  onUpdateCantidad: (uid: string, delta: number) => void
  onRemoveItem: (uid: string) => void
  onClearCart: () => void
  onSubmit: () => void
  submitting: boolean
}

export const ComandaSidebar: React.FC<Props> = ({
  items,
  mesa,
  pedidoActivo,
  onUpdateCantidad,
  onRemoveItem,
  onClearCart,
  onSubmit,
  submitting,
}) => {
  const totalItemsCount = items.reduce((acc, i) => acc + i.cantidad, 0)
  const totalNuevosItems = items.reduce((acc, i) => acc + i.precio_unitario * i.cantidad, 0)

  const isRonda = !!pedidoActivo && !['PAGADO', 'CERRADO', 'CANCELADO'].includes(pedidoActivo.estado)
  const nextRondaNumero = pedidoActivo
    ? Math.max(...pedidoActivo.detalles.map((d) => d.ronda), 1) + 1
    : 1

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-3.5 flex flex-col h-full shadow-2xl overflow-hidden">
      {/* Cabecera de la Mesa */}
      <div className="pb-2.5 mb-2.5 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-orange-600/30 border border-orange-500/50 flex items-center justify-center text-orange-400">
            <Utensils className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-orange-400 block leading-none">
              Comanda de Salón
            </span>
            <p className="text-sm font-black text-white mt-0.5">
              {mesa ? `Mesa #${mesa.numero}` : 'Ninguna mesa elegida'}
            </p>
          </div>
        </div>

        {items.length > 0 && (
          <button
            type="button"
            onClick={onClearCart}
            title="Vaciar comanda"
            className="text-slate-500 hover:text-red-400 p-1.5 rounded-lg transition cursor-pointer hover:bg-slate-800"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Si hay pedido activo en esta mesa, mostrar lo que ya se ordenó */}
      {isRonda && pedidoActivo && (
        <div className="mb-2.5 p-2 rounded-2xl bg-amber-950/30 border border-amber-800/50 max-h-32 overflow-y-auto">
          <div className="flex items-center justify-between text-[11px] font-bold text-amber-300 mb-1">
            <span className="flex items-center gap-1">
              <Layers className="w-3 h-3" /> En mesa (Orden #{pedidoActivo.consecutivo})
            </span>
            <span className="bg-amber-600/50 text-white px-1.5 py-0.2 rounded text-[9px] font-bold">
              {pedidoActivo.estado}
            </span>
          </div>

          <div className="space-y-1">
            {pedidoActivo.detalles.map((det) => (
              <div
                key={det.id}
                className="flex items-center justify-between text-[11px] text-slate-300 bg-slate-950/70 px-2 py-0.5 rounded"
              >
                <div className="truncate flex-1">
                  <span className="font-bold text-amber-200">{det.cantidad}×</span>{' '}
                  <span>{det.producto_nombre}</span>
                  {Array.isArray(det.variacion_snapshot?.modificaciones) &&
                    det.variacion_snapshot.modificaciones.length > 0 && (
                      <span className="text-[10px] text-slate-400 ml-1">
                        ({det.variacion_snapshot.modificaciones.join(', ')})
                      </span>
                    )}
                </div>
                <span className="text-[9px] font-mono text-slate-400 px-1 rounded bg-slate-900 border border-slate-800 ml-1 shrink-0">
                  R{det.ronda}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Lista de nuevos ítems a enviar con precios */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1 min-h-[120px]">
        {items.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-4 text-slate-500">
            <Utensils className="w-7 h-7 stroke-1 text-slate-600 mb-1.5" />
            <p className="text-xs font-semibold text-slate-400">Sin productos aún</p>
            <p className="text-[11px] text-slate-500 mt-0.5">
              {mesa ? 'Toca platos en el menú para agregarlos.' : 'Selecciona una mesa arriba primero.'}
            </p>
          </div>
        ) : (
          items.map((item) => {
            const lineaTotal = item.precio_unitario * item.cantidad
            return (
              <div
                key={item.uid}
                className="p-2.5 rounded-2xl bg-slate-950/80 border border-slate-800 flex flex-col gap-1"
              >
                <div className="flex items-start justify-between gap-1.5">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h5 className="text-xs font-bold text-white truncate mr-1">
                        {item.producto.nombre}
                      </h5>
                      <span className="text-xs font-black font-mono text-emerald-400 shrink-0">
                        ${lineaTotal.toLocaleString('es-CO')}
                      </span>
                    </div>

                    {/* Adiciones con precio */}
                    {item.variacion.adiciones && item.variacion.adiciones.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-0.5">
                        {item.variacion.adiciones.map((ad) => (
                          <span
                            key={ad.id}
                            className="text-[9px] bg-emerald-950/60 text-emerald-300 border border-emerald-800/60 px-1 py-0.2 rounded font-semibold"
                          >
                            +{ad.nombre} (${ad.precio.toLocaleString('es-CO')})
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Modificaciones sin costo */}
                    {item.variacion.modificaciones && item.variacion.modificaciones.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-0.5">
                        {item.variacion.modificaciones.map((m) => (
                          <span
                            key={m}
                            className="text-[9px] bg-slate-900 text-slate-400 border border-slate-800 px-1 py-0.2 rounded"
                          >
                            {m}
                          </span>
                        ))}
                      </div>
                    )}

                    {item.variacion.es_preparado && (
                      <span className="inline-flex items-center gap-1 text-[9px] font-bold text-amber-400 bg-amber-950/60 border border-amber-800/60 px-1 py-0.2 rounded mt-0.5">
                        <Zap className="w-2.5 h-2.5" /> Preparado Listo
                      </span>
                    )}

                    {item.variacion.notas && (
                      <p className="text-[10px] text-orange-300/80 italic mt-0.5">
                        "{item.variacion.notas}"
                      </p>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => onRemoveItem(item.uid)}
                    className="text-slate-600 hover:text-red-400 p-1 transition cursor-pointer"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Stepper de Cantidad */}
                <div className="flex items-center justify-between pt-1 border-t border-slate-900 text-[10px]">
                  <span className="text-slate-500 font-mono">
                    ${item.precio_unitario.toLocaleString('es-CO')} c/u
                  </span>

                  <div className="flex items-center gap-2 bg-slate-900 px-2 py-0.5 rounded-lg border border-slate-800">
                    <button
                      type="button"
                      onClick={() => onUpdateCantidad(item.uid, -1)}
                      className="w-4 h-4 flex items-center justify-center text-slate-400 hover:text-white transition"
                    >
                      <Minus className="w-2.5 h-2.5" />
                    </button>
                    <span className="text-xs font-black text-white w-4 text-center">
                      {item.cantidad}
                    </span>
                    <button
                      type="button"
                      onClick={() => onUpdateCantidad(item.uid, 1)}
                      className="w-4 h-4 flex items-center justify-center text-slate-400 hover:text-white transition"
                    >
                      <Plus className="w-2.5 h-2.5" />
                    </button>
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Pie con TOTAL CALCULADO EN VIVO Y ENVÍO A COCINA */}
      <div className="pt-2.5 mt-2 border-t border-slate-800 flex flex-col gap-2">
        <div className="bg-slate-950/90 border border-slate-800 rounded-xl p-2.5 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block leading-none">
              Total Comanda ({totalItemsCount} ítems)
            </span>
            <span className="text-[10px] text-slate-500">IVA 19% incluido</span>
          </div>
          <span className="text-lg font-black font-mono text-emerald-400">
            ${totalNuevosItems.toLocaleString('es-CO')}
          </span>
        </div>

        <button
          type="button"
          disabled={items.length === 0 || submitting || !mesa}
          onClick={onSubmit}
          className={`w-full py-3 rounded-xl font-black text-xs sm:text-sm text-white shadow-xl transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-40 disabled:pointer-events-none active:scale-98 ${
            isRonda
              ? 'bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 shadow-amber-600/30'
              : 'bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 shadow-orange-600/30'
          }`}
        >
          {submitting ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Transmitiendo a Cocina...</span>
            </>
          ) : isRonda ? (
            <>
              <Layers className="w-4 h-4" />
              <span>Enviar Ronda {nextRondaNumero} • ${totalNuevosItems.toLocaleString('es-CO')}</span>
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span>Enviar a Cocina • ${totalNuevosItems.toLocaleString('es-CO')}</span>
            </>
          )}
        </button>

        {!mesa && items.length > 0 && (
          <p className="text-[10px] text-amber-400 text-center font-medium">
            ⚠️ Toca una mesa (1-9) arriba antes de enviar el pedido.
          </p>
        )}
      </div>
    </div>
  )
}
