import React from 'react'
import type { Mesa, Pedido } from '../../types/mesero'
import { Flame, Clock, Plus, Utensils } from 'lucide-react'

interface Props {
  mesas: Mesa[]
  pedidosActivos: Pedido[]
  mesaSeleccionada: Mesa | null
  onSelectMesa: (mesa: Mesa) => void
}

export const MesaSelector: React.FC<Props> = ({
  mesas,
  pedidosActivos,
  mesaSeleccionada,
  onSelectMesa,
}) => {
  return (
    <div className="w-full">
      {/* Barra superior compacta con estado de la mesa seleccionada */}
      <div className="flex items-center justify-between mb-1.5 px-0.5">
        <div className="flex items-center gap-1.5">
          <Utensils className="w-3.5 h-3.5 text-orange-500" />
          <span className="text-[11px] font-black uppercase tracking-wider text-slate-200">
            {mesaSeleccionada ? (
              <span className="text-orange-400">Mesa #{mesaSeleccionada.numero} Seleccionada</span>
            ) : (
              'Elige una mesa para tomar pedido'
            )}
          </span>
        </div>

        {/* Mini leyenda semáforo */}
        <div className="flex items-center gap-2 text-[10px] font-semibold text-slate-400">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Libre
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span> Cocina
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-500"></span> Servida
          </span>
        </div>
      </div>

      {/* Cuadrícula compacta de 9 Mesas (Altamente optimizada para teléfonos) */}
      <div className="grid grid-cols-9 gap-1 sm:gap-1.5">
        {mesas.map((mesa) => {
          const isSelected = mesaSeleccionada?.id === mesa.id
          const pedido = pedidosActivos.find(
            (p) => p.mesa_id === mesa.id && !['PAGADO', 'CERRADO', 'CANCELADO'].includes(p.estado)
          )

          let colorBg = 'bg-slate-900 border-slate-800 text-slate-400'
          let dotColor = 'bg-slate-600'
          let icon = <Plus className="w-2.5 h-2.5" />

          if (mesa.estado === 'DISPONIBLE') {
            colorBg = 'bg-emerald-950/40 border-emerald-800/70 text-emerald-300 hover:bg-emerald-950/80'
            dotColor = 'bg-emerald-500'
          } else if (mesa.estado === 'EN_CURSO') {
            colorBg = 'bg-amber-950/50 border-amber-600/80 text-amber-200 hover:bg-amber-950/80'
            dotColor = 'bg-amber-500'
            icon = <Flame className="w-2.5 h-2.5 text-amber-400 animate-pulse" />
          } else if (mesa.estado === 'OCUPADA') {
            colorBg = 'bg-red-950/50 border-red-700/80 text-red-200 hover:bg-red-950/80'
            dotColor = 'bg-red-500'
            icon = <Clock className="w-2.5 h-2.5 text-red-400" />
          }

          const rondasCount = pedido ? Math.max(...pedido.detalles.map((d) => d.ronda), 1) : 0

          return (
            <button
              key={mesa.id}
              type="button"
              onClick={() => onSelectMesa(mesa)}
              className={`py-1.5 px-0.5 rounded-xl border flex flex-col items-center justify-center transition active:scale-95 cursor-pointer relative ${
                isSelected
                  ? 'ring-2 ring-orange-500 ring-offset-1 ring-offset-slate-950 bg-orange-950/50 border-orange-500 text-white font-bold scale-105 z-10'
                  : colorBg
              }`}
            >
              {/* Punto de estado y Ronda */}
              <div className="flex items-center justify-between w-full px-1 mb-0.5">
                <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`}></span>
                {rondasCount > 1 ? (
                  <span className="text-[8px] font-bold bg-orange-600 text-white px-0.5 rounded leading-none">
                    R{rondasCount}
                  </span>
                ) : (
                  <span className="opacity-70">{icon}</span>
                )}
              </div>

              {/* Número de Mesa */}
              <span className="text-sm sm:text-base font-black leading-none">{mesa.numero}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
