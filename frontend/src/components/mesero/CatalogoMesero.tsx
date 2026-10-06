import React, { useState, useMemo } from 'react'
import type { Categoria, Producto } from '../../types/mesero'
import { Search, Plus, SlidersHorizontal, AlertCircle, Sparkles } from 'lucide-react'

interface Props {
  categorias: Categoria[]
  productos: Producto[]
  onSelectProducto: (producto: Producto) => void
  onQuickAdd: (producto: Producto) => void
  tipoConsumo?: 'LOCAL' | 'LLEVAR'
}

export const CatalogoMesero: React.FC<Props> = ({
  categorias,
  productos,
  onSelectProducto,
  onQuickAdd,
  tipoConsumo = 'LOCAL',
}) => {
  const [catSeleccionada, setCatSeleccionada] = useState<number | null>(null)
  const [busqueda, setBusqueda] = useState('')

  const getCategoryEmoji = (nombre: string) => {
    const n = nombre.toUpperCase()
    if (n.includes('HAMBURGUESA')) return '🍔'
    if (n.includes('PERRO')) return '🌭'
    if (n.includes('ACOMPAÑA') || n.includes('PAPA')) return '🍟'
    if (n.includes('BEBIDA')) return '🥤'
    if (n.includes('POSTRE')) return '🍰'
    return '🍽️'
  }

  const categoriasValidas = useMemo(() => {
    return categorias.filter(
      (c) => c.id !== 99 && !c.nombre.toUpperCase().includes('SERVICIO') && !c.nombre.toUpperCase().includes('EMPAQUE')
    )
  }, [categorias])

  const productosFiltrados = useMemo(() => {
    return productos.filter((p) => {
      if (p.categoria_id === 99) return false
      const n = (p.nombre || '').toLowerCase()
      if (n.startsWith('empaque') || n.includes('desechable') || n === 'c1' || n === 'p1') return false
      const matchCat = catSeleccionada === null || p.categoria_id === catSeleccionada
      const matchText =
        p.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
        (p.descripcion && p.descripcion.toLowerCase().includes(busqueda.toLowerCase()))
      return matchCat && matchText
    })
  }, [productos, catSeleccionada, busqueda])

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Barra de Búsqueda y Categorías Rápidas */}
      <div className="space-y-2 mb-3 shrink-0">
        {/* Buscador */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar hamburguesa, bebida, papas..."
            className="w-full pl-9 pr-3 py-2 bg-slate-900/90 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-orange-500 shadow-inner"
          />
        </div>

        {/* Selector de Categorías Grande y Táctil */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1.5 scrollbar-none">
          <button
            type="button"
            onClick={() => setCatSeleccionada(null)}
            className={`px-3.5 py-2 rounded-2xl border text-xs font-bold whitespace-nowrap transition active:scale-95 cursor-pointer flex items-center gap-1.5 shadow-sm ${
              catSeleccionada === null
                ? 'bg-orange-600 border-orange-500 text-white shadow-lg shadow-orange-600/30'
                : 'bg-slate-900 border-slate-800 text-slate-300 hover:text-white hover:border-slate-700'
            }`}
          >
            <span>🍽️</span>
            <span>Todos ({productosFiltrados.length})</span>
          </button>

          {categoriasValidas.map((cat) => {
            const count = productos.filter((p) => p.categoria_id === cat.id).length
            const isSelected = catSeleccionada === cat.id
            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => setCatSeleccionada(cat.id)}
                className={`px-3.5 py-2 rounded-2xl border text-xs font-black whitespace-nowrap transition active:scale-95 cursor-pointer flex items-center gap-1.5 shadow-sm ${
                  isSelected
                    ? 'bg-orange-600 border-orange-500 text-white shadow-lg shadow-orange-600/30'
                    : 'bg-slate-900 border-slate-800 text-slate-300 hover:text-white hover:border-slate-700'
                }`}
              >
                <span>{getCategoryEmoji(cat.nombre)}</span>
                <span>{cat.nombre}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold ${
                    isSelected ? 'bg-orange-800 text-white' : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {count}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Grid de Productos Táctil con PRECIOS VISIBLES */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5 overflow-y-auto pr-1 flex-1 min-h-0 pb-12 lg:pb-2">
        {productosFiltrados.map((prod) => {
          const disponible = prod.disponible
          const precioBase = Number(prod.precio || 0)
          const recargoLlevar = tipoConsumo === 'LLEVAR' ? Number(prod.recargo_llevar || 0) : 0
          const precioEfectivo = precioBase + recargoLlevar

          return (
            <div
              key={prod.id}
              className={`bg-slate-900/90 border rounded-2xl p-3 flex flex-col justify-between transition relative overflow-hidden group ${
                disponible
                  ? 'border-slate-800 hover:border-orange-500/80 shadow-md hover:shadow-orange-950/20'
                  : 'border-red-950/60 bg-slate-950/70 opacity-60'
              }`}
            >
              {/* Badge de Disponibilidad y Precio */}
              <div className="flex items-center justify-between gap-1 mb-1.5">
                {disponible ? (
                  <span className="text-[10px] font-semibold text-emerald-400 flex items-center gap-1 bg-emerald-950/50 px-1.5 py-0.5 rounded border border-emerald-800/50">
                    <Sparkles className="w-2.5 h-2.5" /> Disponible
                  </span>
                ) : (
                  <span className="text-[10px] font-semibold text-red-400 flex items-center gap-1 bg-red-950/80 px-1.5 py-0.5 rounded border border-red-800/80">
                    <AlertCircle className="w-2.5 h-2.5" /> Agotado
                  </span>
                )}

                {/* Precio del producto visible para el mesero */}
                <div className="flex flex-col items-end">
                  <span
                    className={`text-xs font-black font-mono px-2 py-0.5 rounded-lg border ${
                      tipoConsumo === 'LLEVAR' && recargoLlevar > 0
                        ? 'text-amber-300 bg-amber-950/70 border-amber-600/70'
                        : 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60'
                    }`}
                  >
                    ${precioEfectivo.toLocaleString('es-CO')}
                  </span>
                  {tipoConsumo === 'LLEVAR' && recargoLlevar > 0 && (
                    <span className="text-[9px] text-orange-300 font-semibold mt-0.5">
                      🥡 +${recargoLlevar.toLocaleString('es-CO')} emp.
                    </span>
                  )}
                </div>
              </div>

              {/* Info del Producto */}
              <div className="mb-2">
                <h4 className="text-xs sm:text-sm font-black text-slate-100 group-hover:text-orange-400 transition leading-snug">
                  {prod.nombre}
                </h4>
                {prod.descripcion && (
                  <p className="text-[11px] text-slate-400 line-clamp-2 mt-0.5 leading-tight">
                    {prod.descripcion}
                  </p>
                )}
              </div>

              {/* Botones de Acción Táctiles */}
              <div className="flex items-center gap-1.5 mt-auto pt-2 border-t border-slate-800/80">
                {/* Botón Personalizar (Modificaciones / Adiciones con precio) */}
                <button
                  type="button"
                  onClick={() => onSelectProducto(prod)}
                  disabled={!disponible}
                  title={
                    prod.es_cocina !== false
                      ? 'Personalizar (adiciones, receta, sin cebolla, notas...)'
                      : 'Opciones de bebida (temperatura, hielo, notas...)'
                  }
                  className="flex-1 py-1.5 px-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:pointer-events-none rounded-xl text-[11px] font-bold text-slate-200 hover:text-white transition flex items-center justify-center gap-1 cursor-pointer active:scale-95"
                >
                  <SlidersHorizontal className="w-3 h-3 text-orange-400" />
                  <span>{prod.es_cocina !== false ? 'Modificar' : 'Opciones'}</span>
                </button>

                {/* Botón Agregar Rápido */}
                <button
                  type="button"
                  onClick={() => onQuickAdd(prod)}
                  disabled={!disponible}
                  title="Agregar 1 directo"
                  className="py-1.5 px-2.5 bg-orange-600 hover:bg-orange-500 active:scale-95 disabled:opacity-30 disabled:pointer-events-none rounded-xl text-white font-black text-xs transition shadow-md shadow-orange-600/30 flex items-center justify-center cursor-pointer shrink-0"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
            </div>
          )
        })}

        {productosFiltrados.length === 0 && (
          <div className="col-span-full py-12 text-center text-slate-500 text-xs">
            No se encontraron productos en esta categoría o búsqueda.
          </div>
        )}
      </div>
    </div>
  )
}
