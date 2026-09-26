import React, { useState, useEffect } from 'react'
import type { ValeOut } from '../../types/caja'
import { getVales, cobrarVale } from '../../api/caja'
import { Receipt, X, Check, Loader2, User, Phone, Calendar, CheckCircle2 } from 'lucide-react'

interface Props {
  isOpen: boolean
  onClose: () => void
  onValeCobrado: () => void
}

export const ValesModal: React.FC<Props> = ({ isOpen, onClose, onValeCobrado }) => {
  const [vales, setVales] = useState<ValeOut[]>([])
  const [tab, setTab] = useState<'PENDIENTE' | 'COBRADO'>('PENDIENTE')
  const [loading, setLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fetchVales = async () => {
    try {
      setLoading(true)
      const data = await getVales(tab)
      setVales(data)
    } catch (err: any) {
      console.error('Error cargando vales:', err)
      setError('Error al cargar vales de caja')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      fetchVales()
    }
  }, [isOpen, tab])

  if (!isOpen) return null

  const handleCobrar = async (valeId: number) => {
    try {
      setActionLoading(valeId)
      await cobrarVale(valeId, 'Pago de pagaré en efectivo en caja')
      await fetchVales()
      onValeCobrado()
    } catch (err: any) {
      console.error('Error cobrando vale:', err)
      alert(err.response?.data?.detail || 'Error al cobrar vale')
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-3 sm:p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Cabecera */}
        <div className="p-4 border-b border-slate-800 bg-slate-800/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-600/30 border border-purple-500/40 flex items-center justify-center text-purple-400">
              <Receipt className="w-6 h-6" />
            </div>
            <div>
              <h2 className="font-black text-white text-lg tracking-wide">
                Vales y Pagarés de Crédito
              </h2>
              <p className="text-xs text-slate-400">
                Consumos autorizados a crédito personal pendientes por recaudar
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="px-4 py-2 bg-slate-950/60 border-b border-slate-800 flex items-center gap-2">
          <button
            onClick={() => setTab('PENDIENTE')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
              tab === 'PENDIENTE'
                ? 'bg-purple-600 text-white shadow'
                : 'bg-slate-800/60 text-slate-400 hover:text-white'
            }`}
          >
            Pendientes de Cobro
          </button>
          <button
            onClick={() => setTab('COBRADO')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
              tab === 'COBRADO'
                ? 'bg-emerald-600 text-white shadow'
                : 'bg-slate-800/60 text-slate-400 hover:text-white'
            }`}
          >
            Historial Cobrados
          </button>
        </div>

        {/* Lista */}
        <div className="p-4 overflow-y-auto space-y-3 flex-1">
          {error && (
            <div className="p-3 bg-rose-950/80 border border-rose-800 text-rose-300 rounded-xl text-xs">
              {error}
            </div>
          )}
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-purple-400 animate-spin mb-2" />
              <span className="text-xs text-slate-400 font-semibold">Cargando vales...</span>
            </div>
          ) : vales.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs">
              No hay vales {tab.toLowerCase()}s registrados en el sistema.
            </div>
          ) : (
            vales.map((v) => (
              <div
                key={v.id}
                className="bg-slate-950 p-4 rounded-2xl border border-slate-800 hover:border-slate-700 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-sm flex items-center gap-1.5">
                      <User className="w-4 h-4 text-purple-400" />
                      {v.cliente_nombre}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                      Vale #{v.id} • Pedido #{v.pedido_id}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                    {v.cliente_cedula && <span>C.C: {v.cliente_cedula}</span>}
                    {v.cliente_telefono && (
                      <span className="flex items-center gap-1">
                        <Phone className="w-3 h-3" />
                        {v.cliente_telefono}
                      </span>
                    )}
                    <span className="flex items-center gap-1 text-slate-500">
                      <Calendar className="w-3 h-3" />
                      {new Date(v.creado_en).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between sm:justify-end gap-4 shrink-0">
                  <div className="text-right">
                    <span className="text-xs text-slate-400 block">Monto Adeudado</span>
                    <span className="font-black text-lg text-purple-400 font-mono">
                      ${Number(v.monto).toLocaleString('es-CO')} COP
                    </span>
                  </div>

                  {v.estado === 'PENDIENTE' ? (
                    <button
                      disabled={actionLoading === v.id}
                      onClick={() => handleCobrar(v.id)}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg transition active:scale-95 disabled:opacity-50 cursor-pointer"
                    >
                      {actionLoading === v.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Check className="w-4 h-4" />
                      )}
                      <span>Cobrar</span>
                    </button>
                  ) : (
                    <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Cobrado
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
