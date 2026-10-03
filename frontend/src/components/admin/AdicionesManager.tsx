import React, { useState, useEffect } from 'react'
import type { AdicionExtra } from '../../types/mesero'
import { getAdicionesConfigApi, guardarAdicionesConfigApi } from '../../api/admin'
import { Plus, Trash2, Save, RefreshCw, CheckCircle2, XCircle, Sliders, AlertCircle } from 'lucide-react'

const ADICIONES_DEFAULT: AdicionExtra[] = [
  { id: 'ad-tocineta', nombre: 'Tocineta Ahumada', precio: 3000, activo: true },
  { id: 'ad-cheddar', nombre: 'Doble Queso Cheddar', precio: 2500, activo: true },
  { id: 'ad-carne', nombre: 'Carne Extra 125g', precio: 5000, activo: true },
  { id: 'ad-huevo', nombre: 'Huevo Frito', precio: 2000, activo: true },
  { id: 'ad-cebolla-caram', nombre: 'Cebolla Caramelizada', precio: 1500, activo: true },
  { id: 'ad-costeno', nombre: 'Queso Costeño Rallado', precio: 2000, activo: true },
  { id: 'ad-papas', nombre: 'Porción Papas Extra', precio: 4000, activo: true },
]

interface Props {
  onSaved?: () => void
}

export const AdicionesManager: React.FC<Props> = ({ onSaved }) => {
  const [adiciones, setAdiciones] = useState<AdicionExtra[]>([])
  const [loading, setLoading] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [mensaje, setMensaje] = useState<{ tipo: 'ok' | 'error'; texto: string } | null>(null)

  // Form para nueva adición
  const [nuevoNombre, setNuevoNombre] = useState('')
  const [nuevoPrecio, setNuevoPrecio] = useState<number>(2500)

  const cargarAdiciones = async () => {
    try {
      setLoading(true)
      const data = await getAdicionesConfigApi()
      if (Array.isArray(data) && data.length > 0) {
        setAdiciones(data.map((item) => ({ ...item, activo: item.activo !== false })))
      } else {
        setAdiciones(ADICIONES_DEFAULT)
      }
    } catch {
      setAdiciones(ADICIONES_DEFAULT)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    cargarAdiciones()
  }, [])

  const handleToggleActivo = (idx: number) => {
    setAdiciones((prev) => {
      const copy = [...prev]
      copy[idx] = { ...copy[idx], activo: !copy[idx].activo }
      return copy
    })
  }

  const handleModificar = (idx: number, campo: 'nombre' | 'precio', valor: any) => {
    setAdiciones((prev) => {
      const copy = [...prev]
      copy[idx] = { ...copy[idx], [campo]: valor }
      return copy
    })
  }

  const handleEliminar = (idx: number) => {
    const item = adiciones[idx]
    if (window.confirm(`¿Deseas eliminar "${item.nombre}" del catálogo de adiciones?`)) {
      setAdiciones((prev) => prev.filter((_, i) => i !== idx))
    }
  }

  const handleAgregarNueva = (e: React.FormEvent) => {
    e.preventDefault()
    if (!nuevoNombre.trim()) {
      alert('Por favor escribe el nombre de la adición')
      return
    }
    if (nuevoPrecio < 0) {
      alert('El precio no puede ser negativo')
      return
    }

    const slug = 'ad-' + nuevoNombre.trim().toLowerCase().replace(/[^a-z0-9]/g, '-') + '-' + Date.now().toString().slice(-4)
    const nueva: AdicionExtra = {
      id: slug,
      nombre: nuevoNombre.trim(),
      precio: Number(nuevoPrecio),
      activo: true,
    }

    setAdiciones((prev) => [...prev, nueva])
    setNuevoNombre('')
    setNuevoPrecio(2500)
  }

  const handleGuardarTodo = async () => {
    setGuardando(true)
    setMensaje(null)
    try {
      await guardarAdicionesConfigApi(adiciones)
      setMensaje({
        tipo: 'ok',
        texto: '✓ ¡Catálogo de adiciones guardado con éxito! Los meseros verán inmediatamente los cambios en la comanda.',
      })
      setTimeout(() => setMensaje(null), 5000)
      if (onSaved) onSaved()
    } catch (err: any) {
      setMensaje({
        tipo: 'error',
        texto: err.response?.data?.detail || 'Error al guardar el catálogo de adiciones',
      })
    } finally {
      setGuardando(false)
    }
  }

  if (loading) {
    return (
      <div className="py-12 flex flex-col items-center justify-center text-slate-400">
        <RefreshCw className="w-6 h-6 animate-spin text-purple-500 mb-2" />
        <span className="text-xs">Cargando catálogo de adiciones...</span>
      </div>
    )
  }

  const activasCount = adiciones.filter((a) => a.activo !== false).length

  return (
    <div className="space-y-4">
      {/* Banner de explicación */}
      <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl flex items-start gap-2.5">
        <Sliders className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300">
          <p className="font-bold text-white mb-0.5">Control de Adiciones Extra en Comanda</p>
          <p className="text-slate-400 leading-relaxed">
            Aquí configuras las opciones con costo que el mesero puede añadir a un plato (ej. hamburguesa, perro, desgranado).
            Usa el botón de estado para <strong>mostrar u ocultar</strong> cualquier adición al instante sin borrarla.
          </p>
        </div>
      </div>

      {mensaje && (
        <div
          className={`p-3 rounded-xl border text-xs flex items-center gap-2 ${
            mensaje.tipo === 'ok'
              ? 'bg-emerald-950/70 border-emerald-700 text-emerald-300'
              : 'bg-rose-950/70 border-rose-800 text-rose-300'
          }`}
        >
          {mensaje.tipo === 'ok' ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
          <span>{mensaje.texto}</span>
        </div>
      )}

      {/* Lista de Adiciones */}
      <div className="space-y-2">
        <div className="flex items-center justify-between pb-1">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Adiciones configuradas ({adiciones.length} total, {activasCount} activas para meseros):
          </span>
        </div>

        <div className="divide-y divide-slate-800/80 border border-slate-800 rounded-xl overflow-hidden bg-slate-950/50">
          {adiciones.map((ad, idx) => {
            const isActivo = ad.activo !== false
            return (
              <div
                key={ad.id || idx}
                className={`p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition ${
                  isActivo ? 'bg-slate-900/60' : 'bg-slate-950/90 opacity-60'
                }`}
              >
                {/* Nombre y Precio */}
                <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[10px] text-slate-500 mb-0.5">Nombre de la Adición</label>
                    <input
                      type="text"
                      value={ad.nombre}
                      onChange={(e) => handleModificar(idx, 'nombre', e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white font-bold focus:outline-none focus:border-purple-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate-500 mb-0.5">Precio al Cliente ($ COP)</label>
                    <div className="relative">
                      <span className="absolute left-2.5 top-1.5 text-xs font-mono text-emerald-400 font-bold">$</span>
                      <input
                        type="number"
                        step="500"
                        min="0"
                        value={ad.precio}
                        onChange={(e) => handleModificar(idx, 'precio', parseFloat(e.target.value) || 0)}
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-6 pr-2.5 py-1.5 text-xs text-emerald-400 font-mono font-bold focus:outline-none focus:border-purple-500"
                      />
                    </div>
                  </div>
                </div>

                {/* Switch Activo / Oculto y Botón Eliminar */}
                <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                  <button
                    type="button"
                    onClick={() => handleToggleActivo(idx)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition cursor-pointer border ${
                      isActivo
                        ? 'bg-emerald-950/70 border-emerald-600 text-emerald-300 hover:bg-emerald-900/80 shadow-sm'
                        : 'bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-700'
                    }`}
                    title={isActivo ? 'Hacer clic para ocultar de la comanda' : 'Hacer clic para mostrar en la comanda'}
                  >
                    {isActivo ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Visible en Comanda</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-3.5 h-3.5 text-slate-400" />
                        <span>Oculto</span>
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    onClick={() => handleEliminar(idx)}
                    className="p-1.5 bg-rose-950/50 hover:bg-rose-900 border border-rose-800/80 text-rose-300 hover:text-white rounded-lg transition cursor-pointer"
                    title="Eliminar del catálogo"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Formulario para Crear Nueva Adición */}
      <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
        <span className="text-xs font-bold uppercase tracking-wider text-purple-400 block">
          + Agregar Nueva Adición al Menú:
        </span>
        <form onSubmit={handleAgregarNueva} className="flex flex-col sm:flex-row sm:items-end gap-2">
          <div className="flex-1">
            <label className="block text-[10px] text-slate-400 mb-0.5">Nombre de la Adición</label>
            <input
              type="text"
              value={nuevoNombre}
              onChange={(e) => setNuevoNombre(e.target.value)}
              placeholder="ej. Jalapeños Extra, Salsa de Ajo..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-semibold"
            />
          </div>
          <div className="w-full sm:w-36">
            <label className="block text-[10px] text-slate-400 mb-0.5">Precio ($ COP)</label>
            <input
              type="number"
              step="500"
              min="0"
              value={nuevoPrecio}
              onChange={(e) => setNuevoPrecio(parseFloat(e.target.value) || 0)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-emerald-400 font-mono font-bold focus:outline-none focus:border-purple-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-1.5 bg-purple-600 hover:bg-purple-500 active:scale-95 text-white font-bold rounded-lg text-xs flex items-center justify-center gap-1.5 transition cursor-pointer shrink-0"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Agregar</span>
          </button>
        </form>
      </div>

      {/* Botón Guardar Cambios */}
      <div className="pt-2 flex items-center justify-end">
        <button
          type="button"
          disabled={guardando}
          onClick={handleGuardarTodo}
          className="py-2.5 px-6 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 active:scale-95 text-white font-black text-xs rounded-xl shadow-xl shadow-purple-950/50 flex items-center gap-2 cursor-pointer transition disabled:opacity-50"
        >
          {guardando ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Guardando Adiciones...</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>Guardar Catálogo de Adiciones</span>
            </>
          )}
        </button>
      </div>
    </div>
  )
}
