import React from 'react'
import type { CanalVenta } from '../../types/mesero'
import { Utensils, ShoppingBag, Bike, Smartphone } from 'lucide-react'

interface Props {
  canal: CanalVenta
  onChangeCanal: (c: CanalVenta) => void
  cliente: string
  onChangeCliente: (v: string) => void
  telefono: string
  onChangeTelefono: (v: string) => void
  direccion: string
  onChangeDireccion: (v: string) => void
  didiOrdenId: string
  onChangeDidiOrdenId: (v: string) => void
}

export const CanalSelector: React.FC<Props> = ({
  canal,
  onChangeCanal,
  cliente,
  onChangeCliente,
  telefono,
  onChangeTelefono,
  direccion,
  onChangeDireccion,
  didiOrdenId,
  onChangeDidiOrdenId,
}) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-3.5 mb-3 shadow-lg">
      <div className="flex items-center justify-between gap-2 overflow-x-auto pb-1 sm:pb-0">
        <button
          type="button"
          onClick={() => onChangeCanal('MESA')}
          className={`flex-1 min-w-[90px] py-2 px-3 rounded-xl border font-bold text-xs flex items-center justify-center gap-2 transition active:scale-95 cursor-pointer ${
            canal === 'MESA'
              ? 'bg-orange-600 border-orange-500 text-white shadow-lg shadow-orange-600/30'
              : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
          }`}
        >
          <Utensils className="w-3.5 h-3.5" />
          <span>Mesa</span>
        </button>

        <button
          type="button"
          onClick={() => onChangeCanal('MOSTRADOR')}
          className={`flex-1 min-w-[90px] py-2 px-3 rounded-xl border font-bold text-xs flex items-center justify-center gap-2 transition active:scale-95 cursor-pointer ${
            canal === 'MOSTRADOR'
              ? 'bg-orange-600 border-orange-500 text-white shadow-lg shadow-orange-600/30'
              : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
          }`}
        >
          <ShoppingBag className="w-3.5 h-3.5" />
          <span>Mostrador</span>
        </button>

        <button
          type="button"
          onClick={() => onChangeCanal('DOMICILIO')}
          className={`flex-1 min-w-[90px] py-2 px-3 rounded-xl border font-bold text-xs flex items-center justify-center gap-2 transition active:scale-95 cursor-pointer ${
            canal === 'DOMICILIO'
              ? 'bg-orange-600 border-orange-500 text-white shadow-lg shadow-orange-600/30'
              : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
          }`}
        >
          <Bike className="w-3.5 h-3.5" />
          <span>Domicilio</span>
        </button>

        <button
          type="button"
          onClick={() => onChangeCanal('DIDI')}
          className={`flex-1 min-w-[90px] py-2 px-3 rounded-xl border font-bold text-xs flex items-center justify-center gap-2 transition active:scale-95 cursor-pointer ${
            canal === 'DIDI'
              ? 'bg-orange-600 border-orange-500 text-white shadow-lg shadow-orange-600/30'
              : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
          }`}
        >
          <Smartphone className="w-3.5 h-3.5" />
          <span>DiDi Food</span>
        </button>
      </div>

      {/* Campos para Domicilio */}
      {canal === 'DOMICILIO' && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-800/80">
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">Nombre Cliente</label>
            <input
              type="text"
              value={cliente}
              onChange={(e) => onChangeCliente(e.target.value)}
              placeholder="ej. Carlos Pérez"
              className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-600 focus:outline-none focus:border-orange-500"
            />
          </div>
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">Teléfono</label>
            <input
              type="tel"
              value={telefono}
              onChange={(e) => onChangeTelefono(e.target.value)}
              placeholder="ej. 312 345 6789"
              className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-600 focus:outline-none focus:border-orange-500"
            />
          </div>
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">
              Dirección de Entrega <span className="text-orange-400">*</span>
            </label>
            <input
              type="text"
              value={direccion}
              onChange={(e) => onChangeDireccion(e.target.value)}
              placeholder="ej. Calle 5 # 34-12 Apto 301"
              className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-600 focus:outline-none focus:border-orange-500"
            />
          </div>
        </div>
      )}

      {/* Campos para DiDi */}
      {canal === 'DIDI' && (
        <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row items-center gap-3">
          <div className="w-full sm:w-1/2">
            <label className="block text-[11px] font-semibold text-amber-400 mb-1">
              Número de Orden DiDi Food (Obligatorio) <span className="text-orange-400">*</span>
            </label>
            <input
              type="text"
              value={didiOrdenId}
              onChange={(e) => onChangeDidiOrdenId(e.target.value)}
              placeholder="ej. #DIDI-9842"
              className="w-full px-3 py-1.5 bg-slate-950 border border-amber-800/60 rounded-lg text-xs font-mono font-bold text-amber-200 placeholder-slate-600 focus:outline-none focus:border-amber-500"
            />
          </div>
          <p className="text-[11px] text-slate-400 italic">
            El repartidor llegará con este código de orden para reclamar el pedido en despacho.
          </p>
        </div>
      )}
    </div>
  )
}
