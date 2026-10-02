import React, { useState, useEffect } from 'react'
import type { Producto, PreparadoItem, AdicionExtra } from '../../types/mesero'
import { getPreparadosDisponiblesApi } from '../../api/mesero'
import { X, Check, Plus, Minus, Zap } from 'lucide-react'

interface Props {
  producto: Producto | null
  onClose: () => void
  onAdd: (
    producto: Producto,
    cantidad: number,
    variacion: {
      notas?: string
      modificaciones?: string[]
      adiciones?: AdicionExtra[]
      es_preparado?: boolean
      preparado_id?: number
    },
    precioUnitarioCalculado: number
  ) => void
}

// Lista de adiciones estándar de Mr. Burger con precio (solo para cocina)
const ADICIONES_DISPONIBLES: AdicionExtra[] = [
  { id: 'ad-tocineta', nombre: 'Tocineta Ahumada', precio: 3000 },
  { id: 'ad-cheddar', nombre: 'Doble Queso Cheddar', precio: 2500 },
  { id: 'ad-carne', nombre: 'Carne Extra 125g', precio: 5000 },
  { id: 'ad-huevo', nombre: 'Huevo Frito', precio: 2000 },
  { id: 'ad-cebolla-caram', nombre: 'Cebolla Caramelizada', precio: 1500 },
  { id: 'ad-costeno', nombre: 'Queso Costeño Rallado', precio: 2000 },
  { id: 'ad-papas', nombre: 'Porción Papas Extra', precio: 4000 },
]

// Lista de modificaciones fallback para cocina (cuando no hay receta detallada)
const MODIFICACIONES_COMUNES = [
  'Sin cebolla',
  'Sin tomate',
  'Sin lechuga',
  'Sin ripio / papitas',
  'Sin salsas',
  'Salsas aparte',
  'Carne bien asada',
  'Término medio',
  'Papas sin sal',
]

// Opciones específicas para bebidas / productos que no son de cocina
const PREFERENCIAS_BEBIDA = [
  'Bien fría / Con hielo',
  'Sin hielo',
  'Al clima',
  'Con vaso adicional',
  'Con rodaja de limón',
  'Azúcar aparte',
]

export const VariacionModal: React.FC<Props> = ({ producto, onClose, onAdd }) => {
  const [cantidad, setCantidad] = useState(1)
  const [modificaciones, setModificaciones] = useState<string[]>([])
  const [adiciones, setAdiciones] = useState<AdicionExtra[]>([])
  const [notas, setNotas] = useState('')
  const [preparadoDisponible, setPreparadoDisponible] = useState<PreparadoItem | null>(null)
  const [usarPreparado, setUsarPreparado] = useState(false)

  const esCocina = producto ? producto.es_cocina !== false : true

  // Opciones dinámicas según receta configurada por el admin
  const opcionesModificacion = React.useMemo(() => {
    if (!producto) return []
    if (!esCocina) return PREFERENCIAS_BEBIDA

    if (producto.ingredientes_receta && producto.ingredientes_receta.length > 0) {
      const sinIngredientes = producto.ingredientes_receta.map((ing) => `Sin ${ing}`)
      const adicionales: string[] = []
      const textoReceta = producto.ingredientes_receta.map((i) => i.toLowerCase()).join(' ')
      if (textoReceta.includes('carne') || textoReceta.includes('res') || textoReceta.includes('pollo')) {
        adicionales.push('Carne bien asada', 'Término medio')
      }
      if (textoReceta.includes('salsa')) {
        adicionales.push('Salsas aparte')
      }
      if (textoReceta.includes('papa')) {
        adicionales.push('Papas sin sal')
      }
      return [...sinIngredientes, ...adicionales]
    }

    return MODIFICACIONES_COMUNES
  }, [producto, esCocina])

  useEffect(() => {
    if (!producto) return
    setCantidad(1)
    setModificaciones([])
    setAdiciones([])
    setNotas('')
    setUsarPreparado(false)

    // Buscar si hay preparado caliente listo en cocina (solo cocina)
    if (!esCocina) {
      setPreparadoDisponible(null)
      return
    }

    const buscarPrep = async () => {
      try {
        const preps = await getPreparadosDisponiblesApi(producto.id)
        if (preps && preps.length > 0) {
          setPreparadoDisponible(preps[0])
        } else {
          setPreparadoDisponible(null)
        }
      } catch {
        setPreparadoDisponible(null)
      }
    }

    buscarPrep()
  }, [producto, esCocina])

  if (!producto) return null

  const precioBase = Number(producto.precio || 0)
  const totalAdicionesUnitario = adiciones.reduce((acc, ad) => acc + ad.precio, 0)
  const precioUnitarioTotal = precioBase + totalAdicionesUnitario
  const totalGeneral = precioUnitarioTotal * cantidad

  const toggleMod = (mod: string) => {
    setModificaciones((prev) =>
      prev.includes(mod) ? prev.filter((m) => m !== mod) : [...prev, mod]
    )
  }

  const toggleAdicion = (ad: AdicionExtra) => {
    setAdiciones((prev) =>
      prev.some((a) => a.id === ad.id) ? prev.filter((a) => a.id !== ad.id) : [...prev, ad]
    )
  }

  const handleConfirm = () => {
    onAdd(
      producto,
      cantidad,
      {
        modificaciones: modificaciones.length > 0 ? modificaciones : undefined,
        adiciones: adiciones.length > 0 ? adiciones : undefined,
        notas: notas.trim() || undefined,
        es_preparado: usarPreparado,
        preparado_id: usarPreparado && preparadoDisponible ? preparadoDisponible.id : undefined,
      },
      precioUnitarioTotal
    )
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-lg overflow-hidden shadow-2xl flex flex-col max-h-[92vh]">
        {/* Cabecera del Producto con Precio Base */}
        <div className="p-4 border-b border-slate-800 flex items-start justify-between bg-slate-950/80">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-orange-500"></span>
              <span className="text-[10px] uppercase font-bold tracking-wider text-orange-400">
                Personalizar Pedido
              </span>
            </div>
            <h3 className="text-xl font-black text-white">{producto.nombre}</h3>
            {producto.descripcion && (
              <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{producto.descripcion}</p>
            )}
          </div>

          <div className="flex flex-col items-end">
            <button
              type="button"
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition cursor-pointer mb-1"
            >
              <X className="w-4 h-4" />
            </button>
            <span className="text-sm font-black text-emerald-400 bg-emerald-950/60 border border-emerald-800/80 px-2 py-0.5 rounded-lg">
              ${precioBase.toLocaleString('es-CO')}
            </span>
          </div>
        </div>

        {/* Contenido scrolleable */}
        <div className="p-4 space-y-4 overflow-y-auto flex-1">
          {/* Alerta inteligente de Preparado Disponible */}
          {preparadoDisponible && (
            <div
              className={`p-3.5 rounded-2xl border transition cursor-pointer flex items-center justify-between ${
                usarPreparado
                  ? 'bg-amber-950/70 border-amber-500 shadow-lg shadow-amber-950/40'
                  : 'bg-amber-950/30 border-amber-800/60 hover:bg-amber-950/50'
              }`}
              onClick={() => setUsarPreparado(!usarPreparado)}
            >
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
                  <Zap className="w-5 h-5 text-amber-400 animate-bounce" />
                </div>
                <div>
                  <p className="text-xs font-bold text-amber-200 flex items-center gap-1.5">
                    <span>¡1× Preparado listo en cocina!</span>
                    <span className="text-[10px] bg-amber-600/60 text-white px-1.5 py-0.2 rounded font-mono">
                      Hace {preparadoDisponible.minutos_espera}m
                    </span>
                  </p>
                  <p className="text-[11px] text-amber-300/80">
                    Ahorra 10 min de espera en cocina. El cocinero solo lo calienta y entrega.
                  </p>
                </div>
              </div>

              <div
                className={`w-6 h-6 rounded-lg flex items-center justify-center border transition ${
                  usarPreparado
                    ? 'bg-amber-500 border-amber-400 text-slate-950'
                    : 'border-amber-700/80 bg-slate-900'
                }`}
              >
                {usarPreparado && <Check className="w-4 h-4 stroke-[3]" />}
              </div>
            </div>
          )}

          {/* 1. SECCIÓN: ADICIONES CON PRECIO EXTRA (Solo productos de cocina) */}
          {producto?.permite_adiciones !== false && esCocina && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                  <Plus className="w-3.5 h-3.5" />
                  <span>Adiciones Extra (Con Costo)</span>
                </label>
                {totalAdicionesUnitario > 0 && (
                  <span className="text-xs font-bold text-emerald-400">
                    +${totalAdicionesUnitario.toLocaleString('es-CO')}
                  </span>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {ADICIONES_DISPONIBLES.map((ad) => {
                  const isSelected = adiciones.some((a) => a.id === ad.id)
                  return (
                    <button
                      key={ad.id}
                      type="button"
                      onClick={() => toggleAdicion(ad)}
                      className={`p-2 rounded-xl border text-xs font-medium transition active:scale-95 cursor-pointer flex items-center justify-between ${
                        isSelected
                          ? 'bg-emerald-950/70 border-emerald-500 text-emerald-200 shadow-md shadow-emerald-950/40'
                          : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      <span className="truncate">{ad.nombre}</span>
                      <span
                        className={`text-[11px] font-bold font-mono px-1.5 py-0.5 rounded ${
                          isSelected ? 'bg-emerald-600 text-white' : 'text-emerald-400 bg-emerald-950/60'
                        }`}
                      >
                        +${ad.precio.toLocaleString('es-CO')}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {/* 2. SECCIÓN: MODIFICACIONES Y QUITAR (Sin costo) / PREFERENCIAS */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-orange-400 mb-2">
              {esCocina ? 'Quitar / Modificar Receta (Sin Costo)' : 'Preferencias de Servicio (Sin Costo)'}
            </label>
            <div className="flex flex-wrap gap-1.5">
              {opcionesModificacion.map((mod) => {
                const active = modificaciones.includes(mod)
                return (
                  <button
                    key={mod}
                    type="button"
                    onClick={() => toggleMod(mod)}
                    className={`px-3 py-1.5 rounded-xl border text-xs font-medium transition active:scale-95 cursor-pointer flex items-center gap-1.5 ${
                      active
                        ? 'bg-orange-600 border-orange-500 text-white shadow-md shadow-orange-600/30'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                    }`}
                  >
                    {active && <Check className="w-3 h-3" />}
                    <span>{mod}</span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* 3. SECCIÓN: NOTAS LIBRES */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
              {esCocina ? 'Nota Libre para Plancha / Cocina' : 'Nota Especial para Servicio'}
            </label>
            <input
              type="text"
              value={notas}
              onChange={(e) => setNotas(e.target.value)}
              placeholder={
                esCocina
                  ? 'ej. Pan muy tostado, poca salsa tártara, etc.'
                  : 'ej. Servir con pitillo, vaso con hielo, etc.'
              }
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-600 focus:outline-none focus:border-orange-500"
            />
          </div>

          {/* Selector de Cantidad */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-800">
            <div>
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                Cantidad
              </span>
              <span className="text-[11px] text-slate-500">
                ${precioUnitarioTotal.toLocaleString('es-CO')} c/u
              </span>
            </div>

            <div className="flex items-center gap-3 bg-slate-950 p-1.5 rounded-xl border border-slate-800">
              <button
                type="button"
                onClick={() => setCantidad((c) => Math.max(1, c - 1))}
                className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-300 hover:text-white transition cursor-pointer"
              >
                <Minus className="w-4 h-4" />
              </button>
              <span className="text-base font-black text-white w-6 text-center">{cantidad}</span>
              <button
                type="button"
                onClick={() => setCantidad((c) => c + 1)}
                className="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-300 hover:text-white transition cursor-pointer"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Pie con Total Calculado en Vivo */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/90 flex items-center gap-2">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-xl text-xs transition cursor-pointer"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            className="flex-[2] py-3 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 active:scale-98 text-white font-black rounded-xl text-xs shadow-xl shadow-orange-600/30 transition flex items-center justify-center gap-2 cursor-pointer"
          >
            <Check className="w-4 h-4" />
            <span>
              Agregar ({cantidad}) • ${totalGeneral.toLocaleString('es-CO')}
            </span>
          </button>
        </div>
      </div>
    </div>
  )
}
