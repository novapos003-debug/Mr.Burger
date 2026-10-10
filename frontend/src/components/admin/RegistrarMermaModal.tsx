import React, { useState, useEffect } from 'react'
import {
  X,
  Flame,
  Package,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Trash2,
} from 'lucide-react'
import api from '../../api/client'
import type { Producto } from '../../types/mesero'

interface IngredienteSimple {
  id: number
  nombre: string
  unidad_base: string
  stock_actual: number
}

interface Props {
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
}

export const RegistrarMermaModal: React.FC<Props> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [tipoSeleccion, setTipoSeleccion] = useState<'INSUMO' | 'PRODUCTO'>('INSUMO')
  const [ingredientes, setIngredientes] = useState<IngredienteSimple[]>([])
  const [productos, setProductos] = useState<Producto[]>([])
  const [loadingData, setLoadingData] = useState(false)

  const [selectedIngredienteId, setSelectedIngredienteId] = useState<number | ''>('')
  const [selectedProductoId, setSelectedProductoId] = useState<number | ''>('')
  const [cantidad, setCantidad] = useState<string>('1')
  const [motivo, setMotivo] = useState<string>('')
  const [submitting, setSubmitting] = useState(false)
  const [feedback, setFeedback] = useState<{ tipo: 'ok' | 'err'; msg: string } | null>(null)

  const motivosRapidos = [
    'Se quemó en plancha',
    'Se cayó al piso',
    'Pan roto / aplastado',
    'Carne / Pollo dañado',
    'Vencimiento / Descompuesto',
    'Error de preparación',
  ]

  useEffect(() => {
    if (isOpen) {
      setLoadingData(true)
      setFeedback(null)
      setCantidad('1')
      setMotivo('')
      setSelectedIngredienteId('')
      setSelectedProductoId('')

      Promise.all([
        api.get('/ingredientes').then((r) => r.data).catch(() => []),
        api.get('/productos').then((r) => r.data).catch(() => []),
      ])
        .then(([ings, prods]) => {
          setIngredientes(ings)
          setProductos(prods)
          if (ings.length > 0) setSelectedIngredienteId(ings[0].id)
          if (prods.length > 0) setSelectedProductoId(prods[0].id)
        })
        .finally(() => setLoadingData(false))
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFeedback(null)

    const cantNum = parseFloat(cantidad)
    if (isNaN(cantNum) || cantNum <= 0) {
      setFeedback({ tipo: 'err', msg: 'Ingresa una cantidad válida mayor a 0' })
      return
    }

    if (!motivo.trim()) {
      setFeedback({ tipo: 'err', msg: 'Escribe el motivo del daño o merma' })
      return
    }

    try {
      setSubmitting(true)
      const payload = {
        ingrediente_id: tipoSeleccion === 'INSUMO' ? Number(selectedIngredienteId) : null,
        producto_id: tipoSeleccion === 'PRODUCTO' ? Number(selectedProductoId) : null,
        cantidad: cantNum,
        motivo: motivo.trim(),
      }

      const res = await api.post('/inventario/merma', payload)
      setFeedback({ tipo: 'ok', msg: res.data?.mensaje || 'Merma registrada exitosamente' })
      if (onSuccess) onSuccess()
      setTimeout(() => {
        onClose()
      }, 1500)
    } catch (err: any) {
      setFeedback({
        tipo: 'err',
        msg: err.response?.data?.detail || err.message || 'Error al registrar merma',
      })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-3 sm:p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Cabecera */}
        <div className="p-4 border-b border-slate-800 bg-rose-950/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400">
              <Trash2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-black text-white text-base sm:text-lg tracking-wide">
                Registrar Daño / Merma
              </h2>
              <p className="text-xs text-rose-300/80">
                Descuento de stock por producto o insumo dañado
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="p-4 sm:p-6 space-y-4 overflow-y-auto">
          {/* Selector Insumo vs Plato Terminado */}
          <div className="flex bg-slate-950 p-1 rounded-2xl border border-slate-800">
            <button
              type="button"
              onClick={() => setTipoSeleccion('INSUMO')}
              className={`flex-1 py-2 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1.5 cursor-pointer ${
                tipoSeleccion === 'INSUMO'
                  ? 'bg-rose-600 text-white shadow-lg shadow-rose-600/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Package className="w-3.5 h-3.5" />
              <span>Insumo / Ingrediente</span>
            </button>
            <button
              type="button"
              onClick={() => setTipoSeleccion('PRODUCTO')}
              className={`flex-1 py-2 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1.5 cursor-pointer ${
                tipoSeleccion === 'PRODUCTO'
                  ? 'bg-rose-600 text-white shadow-lg shadow-rose-600/30'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Flame className="w-3.5 h-3.5" />
              <span>Plato / Menú Completo</span>
            </button>
          </div>

          {loadingData ? (
            <div className="flex items-center justify-center py-8 text-slate-400 text-xs gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-rose-500" />
              <span>Cargando catálogo...</span>
            </div>
          ) : (
            <>
              {/* Selección del Ítem */}
              {tipoSeleccion === 'INSUMO' ? (
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1.5">
                    Seleccionar Insumo Dañado:
                  </label>
                  <select
                    value={selectedIngredienteId}
                    onChange={(e) => setSelectedIngredienteId(Number(e.target.value))}
                    className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm font-semibold text-white focus:outline-none focus:border-rose-500"
                  >
                    {ingredientes.map((ing) => (
                      <option key={ing.id} value={ing.id}>
                        {ing.nombre} (Stock actual: {ing.stock_actual} {ing.unidad_base})
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1.5">
                    Seleccionar Plato Dañado (Descuenta su receta):
                  </label>
                  <select
                    value={selectedProductoId}
                    onChange={(e) => setSelectedProductoId(Number(e.target.value))}
                    className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm font-semibold text-white focus:outline-none focus:border-rose-500"
                  >
                    {productos.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.nombre}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Cantidad */}
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Cantidad a Dar de Baja / Descontar:
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    step="any"
                    min="0.01"
                    value={cantidad}
                    onChange={(e) => setCantidad(e.target.value)}
                    required
                    placeholder="ej. 1"
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm font-mono font-bold text-white focus:outline-none focus:border-rose-500"
                  />
                  <div className="flex gap-1">
                    {['1', '2', '5'].map((v) => (
                      <button
                        key={v}
                        type="button"
                        onClick={() => setCantidad(v)}
                        className="px-2.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-bold transition"
                      >
                        +{v}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Motivos Rápidos */}
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Motivo del Daño / Merma:
                </label>
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {motivosRapidos.map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setMotivo(m)}
                      className={`text-[11px] px-2.5 py-1 rounded-lg border font-medium transition cursor-pointer ${
                        motivo === m
                          ? 'bg-rose-950 border-rose-600 text-rose-300'
                          : 'bg-slate-950/80 border-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
                <input
                  type="text"
                  value={motivo}
                  onChange={(e) => setMotivo(e.target.value)}
                  placeholder="Escribe el motivo detallado..."
                  required
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-600 focus:outline-none focus:border-rose-500"
                />
              </div>

              {/* Feedback */}
              {feedback && (
                <div
                  className={`p-3 rounded-xl flex items-center gap-2 text-xs font-bold ${
                    feedback.tipo === 'ok'
                      ? 'bg-emerald-950/60 border border-emerald-700 text-emerald-300'
                      : 'bg-rose-950/60 border border-rose-700 text-rose-300'
                  }`}
                >
                  {feedback.tipo === 'ok' ? (
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                  ) : (
                    <AlertCircle className="w-4 h-4 shrink-0" />
                  )}
                  <span>{feedback.msg}</span>
                </div>
              )}
            </>
          )}

          {/* Botones de Acción */}
          <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl text-xs font-bold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition cursor-pointer"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting || loadingData}
              className="px-5 py-2.5 rounded-xl text-xs font-black text-white bg-rose-600 hover:bg-rose-500 active:scale-95 shadow-lg shadow-rose-600/30 transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              {submitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
              <span>Registrar Descuento</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
