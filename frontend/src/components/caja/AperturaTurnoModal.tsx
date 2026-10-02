import React, { useState } from 'react'
import { DollarSign, X, Check, Loader2 } from 'lucide-react'

interface Props {
  isOpen: boolean
  onClose: () => void
  onConfirm: (montoInicial: number) => Promise<void>
}

export const AperturaTurnoModal: React.FC<Props> = ({ isOpen, onClose, onConfirm }) => {
  const [monto, setMonto] = useState<number>(100000)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleAbrir = async (e: React.FormEvent) => {
    e.preventDefault()
    if (monto < 0) {
      setError('El monto inicial no puede ser negativo')
      return
    }
    try {
      setLoading(true)
      setError(null)
      await onConfirm(monto)
      onClose()
    } catch (err: any) {
      console.error('Error abriendo turno:', err)
      setError(err.response?.data?.detail || 'Error al abrir turno de caja')
    } finally {
      setLoading(false)
    }
  }

  const basesSugeridas = [50000, 100000, 150000, 200000]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto">
        {/* Cabecera */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-800/40">
          <div className="flex items-center gap-2 text-emerald-400">
            <DollarSign className="w-5 h-5" />
            <h2 className="font-bold text-white text-base">Apertura de Turno de Caja</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Formulario */}
        <form onSubmit={handleAbrir} className="p-5 space-y-4">
          <p className="text-xs text-slate-400 leading-relaxed">
            Ingresa el monto de la base de efectivo inicial (sencillo para cambio) con el que se inicia la jornada en la gaveta de dinero.
          </p>

          {error && (
            <div className="p-3 bg-rose-950/80 border border-rose-800 text-rose-300 rounded-xl text-xs">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wide mb-1.5">
              Base Inicial de Efectivo ($ COP)
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 font-bold">$</span>
              <input
                type="number"
                min="0"
                step="1000"
                value={monto || ''}
                onChange={(e) => setMonto(Number(e.target.value))}
                className="w-full pl-8 pr-4 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-emerald-400 font-mono font-bold text-xl focus:border-emerald-500 focus:outline-none"
                placeholder="100000"
                required
              />
            </div>
          </div>

          {/* Botones de sugerencia rápida */}
          <div>
            <span className="text-[11px] text-slate-400 font-medium">Bases comunes:</span>
            <div className="grid grid-cols-4 gap-2 mt-1">
              {basesSugeridas.map((b) => (
                <button
                  key={b}
                  type="button"
                  onClick={() => setMonto(b)}
                  className={`py-1.5 px-2 rounded-lg text-xs font-bold transition border cursor-pointer ${
                    monto === b
                      ? 'bg-emerald-600/30 border-emerald-500 text-emerald-300'
                      : 'bg-slate-800/60 border-slate-700 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  ${(b / 1000).toLocaleString()}k
                </button>
              ))}
            </div>
          </div>

          <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white transition cursor-pointer"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-1.5 px-5 py-2 rounded-xl font-black text-xs bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg transition active:scale-95 disabled:opacity-50 cursor-pointer"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Check className="w-4 h-4" />
              )}
              Abrir Turno
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
