import React, { useState, useEffect } from 'react'
import type { CanalVenta, Producto, Categoria, AdicionExtra } from '../../types/mesero'
import { getProductosApi, getCategoriasApi } from '../../api/mesero'
import { crearPedidoCaja, enviarPedidoACocina } from '../../api/caja'
import { VariacionModal } from '../mesero/VariacionModal'
import {
  X,
  Store,
  Bike,
  ShoppingBag,
  Plus,
  Minus,
  Send,
  Loader2,
  DollarSign,
  SlidersHorizontal,
  Trash2,
} from 'lucide-react'

interface Props {
  isOpen: boolean
  onClose: () => void
  onPedidoCreado: (pedidoId: number, abrirCobroDirecto: boolean) => void
}

interface ItemCarritoCaja {
  uid: string
  producto: Producto
  cantidad: number
  precio_unitario: number
  variacion: {
    notas?: string
    modificaciones?: string[]
    adiciones?: AdicionExtra[]
    es_preparado?: boolean
    preparado_id?: number
  }
}

export const NuevoPedidoModal: React.FC<Props> = ({ isOpen, onClose, onPedidoCreado }) => {
  const [canal, setCanal] = useState<CanalVenta>('MOSTRADOR')
  const [tipoConsumo, setTipoConsumo] = useState<'LOCAL' | 'LLEVAR'>('LOCAL')
  const [cliente, setCliente] = useState<string>('')
  const [telefono, setTelefono] = useState<string>('')
  const [direccion, setDireccion] = useState<string>('')
  const [didiOrdenId, setDidiOrdenId] = useState<string>('')
  const [notaInterna, setNotaInterna] = useState<string>('')

  // Catálogo
  const [productos, setProductos] = useState<Producto[]>([])
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [categoriaSel, setCategoriaSel] = useState<number | null>(null)
  const [busqueda, setBusqueda] = useState<string>('')
  const [carrito, setCarrito] = useState<ItemCarritoCaja[]>([])
  const [productoParaVariacion, setProductoParaVariacion] = useState<Producto | null>(null)

  const [loading, setLoading] = useState(false)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      setLoading(true)
      Promise.all([getProductosApi(), getCategoriasApi()])
        .then(([prods, cats]) => {
          const prodsValidos = prods.filter(
            (p: Producto) =>
              p.activo &&
              p.categoria_id !== 99 &&
              !p.nombre.toLowerCase().startsWith('empaque') &&
              !p.nombre.toLowerCase().includes('desechable') &&
              p.nombre.toLowerCase() !== 'c1' &&
              p.nombre.toLowerCase() !== 'p1'
          )
          const catsValidas = cats.filter(
            (c) =>
              c.id !== 99 &&
              !c.nombre.toUpperCase().includes('SERVICIO') &&
              !c.nombre.toUpperCase().includes('EMPAQUE')
          )
          setProductos(prodsValidos)
          setCategorias(catsValidas)
          setCategoriaSel(null) // Ver todo el menú al abrir
        })
        .catch((err) => console.error('Error cargando catálogo:', err))
        .finally(() => setLoading(false))

      setCanal('MOSTRADOR')
      setTipoConsumo('LOCAL')
      setCliente('')
      setTelefono('')
      setDireccion('')
      setDidiOrdenId('')
      setNotaInterna('')
      setCarrito([])
      setProductoParaVariacion(null)
      setError(null)
    }
  }, [isOpen])

  if (!isOpen) return null

  const agregarRapido = (prod: Producto) => {
    const idx = carrito.findIndex(
      (item) =>
        item.producto.id === prod.id &&
        (!item.variacion || Object.keys(item.variacion).length === 0)
    )
    if (idx >= 0) {
      modificarCantidad(carrito[idx].uid, 1)
      return
    }
    const newItem: ItemCarritoCaja = {
      uid: `${prod.id}-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      producto: prod,
      cantidad: 1,
      precio_unitario: Number(prod.precio || 0),
      variacion: {},
    }
    setCarrito((prev) => [...prev, newItem])
  }

  const handleAddCustom = (
    prod: Producto,
    cantidad: number,
    variacion: {
      notas?: string
      modificaciones?: string[]
      adiciones?: AdicionExtra[]
      es_preparado?: boolean
      preparado_id?: number
    },
    precioUnitarioCalculado: number
  ) => {
    const newItem: ItemCarritoCaja = {
      uid: `${prod.id}-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      producto: prod,
      cantidad,
      precio_unitario: precioUnitarioCalculado,
      variacion,
    }
    setCarrito((prev) => [...prev, newItem])
  }

  const modificarCantidad = (uid: string, delta: number) => {
    setCarrito((prev) =>
      prev
        .map((item) => {
          if (item.uid === uid) {
            const nueva = item.cantidad + delta
            return nueva > 0 ? { ...item, cantidad: nueva } : null
          }
          return item
        })
        .filter(Boolean) as ItemCarritoCaja[]
    )
  }

  const eliminarItem = (uid: string) => {
    setCarrito((prev) => prev.filter((item) => item.uid !== uid))
  }

  const totalBase = carrito.reduce(
    (sum, item) => sum + item.precio_unitario * item.cantidad,
    0
  )
  const totalEmpaques = tipoConsumo === 'LLEVAR'
    ? carrito.reduce((sum, item) => sum + (Number(item.producto.recargo_llevar || 0) * item.cantidad), 0)
    : 0
  const totalCalculado = totalBase + totalEmpaques

  const productosFiltrados = productos.filter((p) => {
    const matchCat = categoriaSel !== null ? Number(p.categoria_id) === Number(categoriaSel) : true
    const q = busqueda.trim().toLowerCase()
    const matchText = q === '' ? true : p.nombre.toLowerCase().includes(q)
    return matchCat && matchText
  })

  const handleSubmit = async (abrirCobro: boolean) => {
    if (carrito.length === 0) {
      setError('Debes agregar al menos un producto a la orden')
      return
    }

    if (canal === 'DOMICILIO' && !direccion.trim()) {
      setError('La dirección de entrega es obligatoria para domicilios')
      return
    }

    if (canal === 'DIDI' && !didiOrdenId.trim()) {
      setError('El número o código de orden de DiDi es obligatorio')
      return
    }

    try {
      setGuardando(true)
      setError(null)

      const lineas = carrito.map((item) => ({
        producto_id: item.producto.id,
        cantidad: item.cantidad,
        variacion_snapshot: Object.keys(item.variacion || {}).length > 0 ? item.variacion : null,
        preparado_id: item.variacion?.preparado_id,
      }))

      const payload: any = {
        canal,
        tipo_consumo: tipoConsumo,
        lineas,
        nota_interna: notaInterna.trim() || null,
        cliente: cliente.trim() || null,
        telefono: telefono.trim() || null,
        direccion: canal === 'DOMICILIO' ? direccion.trim() : null,
        didi_orden_id: canal === 'DIDI' ? didiOrdenId.trim() : null,
      }

      const pedido = await crearPedidoCaja(payload)
      // Enviar a cocina automáticamente
      await enviarPedidoACocina(pedido.id)

      onPedidoCreado(pedido.id, abrirCobro)
      onClose()
    } catch (err: any) {
      console.error('Error creando pedido en caja:', err)
      setError(err.response?.data?.detail || 'Error al crear pedido')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-2 sm:p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[95vh]">
        {/* Cabecera */}
        <div className="p-4 border-b border-slate-800 bg-slate-800/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
              <Store className="w-6 h-6" />
            </div>
            <div>
              <h2 className="font-black text-white text-lg tracking-wide">
                Nueva Orden en Caja
              </h2>
              <p className="text-xs text-slate-400">
                Atención exclusiva de Mostrador, Domicilio y DiDi Food
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

        {/* Canales Selector */}
        <div className="p-4 border-b border-slate-800 bg-slate-950/70 space-y-3">
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => setCanal('MOSTRADOR')}
              className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl font-bold text-xs border transition cursor-pointer ${
                canal === 'MOSTRADOR'
                  ? 'bg-sky-600 border-sky-500 text-white shadow'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              <Store className="w-4 h-4" />
              <span>Mostrador / Llevar</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setCanal('DOMICILIO')
                setTipoConsumo('LLEVAR')
              }}
              className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl font-bold text-xs border transition cursor-pointer ${
                canal === 'DOMICILIO'
                  ? 'bg-purple-600 border-purple-500 text-white shadow'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              <Bike className="w-4 h-4" />
              <span>Domicilio Teléfono</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setCanal('DIDI')
                setTipoConsumo('LLEVAR')
              }}
              className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl font-bold text-xs border transition cursor-pointer ${
                canal === 'DIDI'
                  ? 'bg-orange-600 border-orange-500 text-white shadow'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              <ShoppingBag className="w-4 h-4" />
              <span>DiDi Food</span>
            </button>
          </div>

          {/* Selector de Tipo de Consumo para Mostrador */}
          {canal === 'MOSTRADOR' && (
            <div className="flex bg-slate-900 p-1 rounded-xl border border-slate-800 gap-1">
              <button
                type="button"
                onClick={() => setTipoConsumo('LOCAL')}
                className={`flex-1 text-xs font-bold py-1.5 rounded-lg transition cursor-pointer ${
                  tipoConsumo === 'LOCAL' ? 'bg-sky-600 text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                🍽️ Comer Aquí (Sin empaque)
              </button>
              <button
                type="button"
                onClick={() => setTipoConsumo('LLEVAR')}
                className={`flex-1 text-xs font-bold py-1.5 rounded-lg transition cursor-pointer ${
                  tipoConsumo === 'LLEVAR' ? 'bg-orange-600 text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                🥡 Para Llevar (Liquida empaque térmico)
              </button>
            </div>
          )}

          {/* Campos específicos según canal */}
          {canal === 'DOMICILIO' && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
              <input
                type="text"
                value={cliente}
                onChange={(e) => setCliente(e.target.value)}
                placeholder="Nombre del Cliente"
                className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none"
              />
              <input
                type="tel"
                value={telefono}
                onChange={(e) => setTelefono(e.target.value)}
                placeholder="Teléfono / Celular"
                className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none"
              />
              <input
                type="text"
                value={direccion}
                onChange={(e) => setDireccion(e.target.value)}
                placeholder="Dirección de Entrega *"
                className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none"
                required
              />
            </div>
          )}

          {canal === 'DIDI' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
              <input
                type="text"
                value={didiOrdenId}
                onChange={(e) => setDidiOrdenId(e.target.value)}
                placeholder="Código / ID de Orden DiDi (ej: #DIDI-891) *"
                className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none"
                required
              />
              <input
                type="text"
                value={cliente}
                onChange={(e) => setCliente(e.target.value)}
                placeholder="Nombre del Repartidor / Cliente (Opcional)"
                className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none"
              />
            </div>
          )}
        </div>

        {/* Contenido dividido: Catálogo (Izquierda) + Resumen Pedido (Derecha) */}
        <div className="flex-1 overflow-hidden grid grid-cols-1 md:grid-cols-12 gap-0">
          {/* Catálogo de Productos */}
          <div className="md:col-span-7 p-4 border-r border-slate-800 flex flex-col overflow-y-auto">
            {/* Buscador & Categorías */}
            <div className="space-y-2 mb-3">
              <input
                type="text"
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                placeholder="Buscar producto (ej: hamburguesa, gaseosa)..."
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-amber-500"
              />
              <div className="flex gap-1.5 overflow-x-auto no-scrollbar pb-1">
                <button
                  type="button"
                  onClick={() => setCategoriaSel(null)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer flex items-center gap-1.5 ${
                    categoriaSel === null
                      ? 'bg-amber-500 text-slate-950 font-black shadow-md'
                      : 'bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700'
                  }`}
                >
                  <span>Todos</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-mono ${
                    categoriaSel === null ? 'bg-black/20 text-slate-950 font-black' : 'bg-slate-700 text-slate-400'
                  }`}>
                    {productos.length}
                  </span>
                </button>
                {categorias.map((c) => {
                  const count = productos.filter((p) => Number(p.categoria_id) === Number(c.id)).length
                  return (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => setCategoriaSel(c.id)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer flex items-center gap-1.5 ${
                        categoriaSel === c.id
                          ? 'bg-amber-500 text-slate-950 font-black shadow-md'
                          : 'bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700'
                      }`}
                    >
                      <span>{c.nombre}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-mono ${
                        categoriaSel === c.id ? 'bg-black/20 text-slate-950 font-black' : 'bg-slate-700 text-slate-400'
                      }`}>
                        {count}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Grid de productos */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 overflow-y-auto max-h-[340px]">
              {loading ? (
                <div className="col-span-3 flex flex-col items-center justify-center py-12 text-slate-500">
                  <Loader2 className="w-8 h-8 text-amber-500 animate-spin mb-2" />
                  <span className="text-xs">Cargando catálogo...</span>
                </div>
              ) : productosFiltrados.length === 0 ? (
                <div className="col-span-2 sm:col-span-3 text-center py-12 text-slate-500">
                  <p className="text-xs">No se encontraron productos en esta categoría o búsqueda.</p>
                  <button
                    type="button"
                    onClick={() => { setCategoriaSel(null); setBusqueda('') }}
                    className="mt-2 text-xs text-amber-400 hover:underline font-bold"
                  >
                    Ver todos los productos
                  </button>
                </div>
              ) : (
                productosFiltrados.map((p) => (
                  <div
                    key={p.id}
                    className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 hover:border-amber-500/60 text-left transition flex flex-col justify-between group"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-1 mb-1">
                        <span className="font-bold text-white text-xs line-clamp-2 group-hover:text-amber-400 transition">
                          {p.nombre}
                        </span>
                        {!p.disponible && (
                          <span
                            className="text-[9px] font-bold text-amber-400 bg-amber-950/80 border border-amber-800/60 px-1 py-0.5 rounded shrink-0"
                            title="Insumos pendientes de registrar en inventario"
                          >
                            Sin stock
                          </span>
                        )}
                      </div>
                      <span className="font-black text-emerald-400 font-mono text-xs block mb-2">
                        ${Number(p.precio).toLocaleString('es-CO')}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 pt-1.5 border-t border-slate-800/80 mt-auto">
                      <button
                        type="button"
                        onClick={() => setProductoParaVariacion(p)}
                        title={
                          p.es_cocina !== false
                            ? 'Personalizar (adiciones, receta, sin cebolla, notas...)'
                            : 'Opciones de bebida (temperatura, hielo, notas...)'
                        }
                        className="flex-1 py-1 px-1.5 bg-slate-800 hover:bg-slate-700 active:scale-95 rounded-lg text-[10px] font-bold text-slate-200 hover:text-white transition flex items-center justify-center gap-1 cursor-pointer"
                      >
                        <SlidersHorizontal className="w-2.5 h-2.5 text-amber-400" />
                        <span>{p.es_cocina !== false ? 'Modificar' : 'Opciones'}</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => agregarRapido(p)}
                        title="Agregar 1 directo"
                        className="py-1 px-2 bg-amber-600 hover:bg-amber-500 active:scale-95 rounded-lg text-white font-bold text-xs transition flex items-center justify-center cursor-pointer shrink-0"
                      >
                        <Plus className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Resumen del Carrito en Caja */}
          <div className="md:col-span-5 p-4 bg-slate-950/40 flex flex-col justify-between overflow-y-auto">
            <div className="space-y-3">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
                Comanda Actual ({carrito.length} ítems)
              </span>

              {carrito.length === 0 ? (
                <div className="text-center py-10 text-slate-600 text-xs">
                  Haz clic en los productos para agregarlos a la comanda.
                </div>
              ) : (
                <div className="space-y-2 max-h-[260px] overflow-y-auto">
                  {carrito.map((item) => {
                    const recargoUnitario = tipoConsumo === 'LLEVAR' ? Number(item.producto.recargo_llevar || 0) : 0
                    const precioUnitarioEfectivo = item.precio_unitario + recargoUnitario
                    const lineaTotal = precioUnitarioEfectivo * item.cantidad

                    return (
                      <div
                        key={item.uid}
                        className="bg-slate-900 p-2.5 rounded-xl border border-slate-800 flex flex-col gap-1.5"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <p className="font-bold text-white text-xs truncate">
                              {item.producto.nombre}
                            </p>
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span className={`text-[11px] font-mono font-bold ${
                                tipoConsumo === 'LLEVAR' && recargoUnitario > 0 ? 'text-amber-300' : 'text-emerald-400'
                              }`}>
                                ${lineaTotal.toLocaleString('es-CO')}
                              </span>
                              {tipoConsumo === 'LLEVAR' && recargoUnitario > 0 && (
                                <span className="text-[10px] text-orange-400 font-medium">
                                  (+$${(recargoUnitario * item.cantidad).toLocaleString('es-CO')} emp.)
                                </span>
                              )}
                              {item.cantidad > 1 && (
                                <span className="text-slate-500 text-[10px] font-sans">
                                  (${precioUnitarioEfectivo.toLocaleString('es-CO')} c/u)
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="flex items-center gap-1 shrink-0">
                            <button
                              type="button"
                              onClick={() => modificarCantidad(item.uid, -1)}
                              className="w-6 h-6 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center cursor-pointer"
                            >
                              <Minus className="w-3 h-3" />
                            </button>
                            <span className="font-black text-xs text-white w-4 text-center">
                              {item.cantidad}
                            </span>
                            <button
                              type="button"
                              onClick={() => modificarCantidad(item.uid, 1)}
                              className="w-6 h-6 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center cursor-pointer"
                            >
                              <Plus className="w-3 h-3" />
                            </button>
                            <button
                              type="button"
                              onClick={() => eliminarItem(item.uid)}
                              className="w-6 h-6 rounded-md bg-rose-950/80 hover:bg-rose-900 text-rose-300 flex items-center justify-center cursor-pointer ml-0.5"
                              title="Eliminar ítem"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        </div>

                        {/* Variaciones detalladas (Adiciones, Quitar / Modificaciones y Notas) */}
                        {((item.variacion.adiciones && item.variacion.adiciones.length > 0) ||
                          (item.variacion.modificaciones && item.variacion.modificaciones.length > 0) ||
                          item.variacion.notas) && (
                          <div className="flex flex-wrap gap-1 pt-1 border-t border-slate-800/60">
                            {item.variacion.adiciones?.map((ad) => (
                              <span
                                key={ad.id}
                                className="text-[9px] bg-emerald-950/80 text-emerald-300 border border-emerald-800/80 px-1.5 py-0.5 rounded font-mono font-bold"
                              >
                                +{ad.nombre} (${ad.precio.toLocaleString('es-CO')})
                              </span>
                            ))}
                            {item.variacion.modificaciones?.map((mod, idx) => (
                              <span
                                key={idx}
                                className="text-[9px] bg-orange-950/80 text-orange-300 border border-orange-800/80 px-1.5 py-0.5 rounded font-medium"
                              >
                                {mod}
                              </span>
                            ))}
                            {item.variacion.notas && (
                              <span className="text-[10px] text-slate-400 italic block w-full">
                                "{item.variacion.notas}"
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Nota Interna */}
              <div>
                <input
                  type="text"
                  value={notaInterna}
                  onChange={(e) => setNotaInterna(e.target.value)}
                  placeholder="Nota interna de cocina (opcional)..."
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none"
                />
              </div>
            </div>

            {/* Total y Botones */}
            <div className="pt-3 border-t border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-slate-400 block">Total Orden:</span>
                  {tipoConsumo === 'LLEVAR' && totalEmpaques > 0 && (
                    <span className="text-[11px] text-orange-400 font-bold block">
                      (Incluye +${totalEmpaques.toLocaleString('es-CO')} en empaques)
                    </span>
                  )}
                </div>
                <span className="text-2xl font-black text-emerald-400 font-mono">
                  ${totalCalculado.toLocaleString('es-CO')} COP
                </span>
              </div>

              {error && (
                <div className="p-2 bg-rose-950/80 border border-rose-800 text-rose-300 rounded-lg text-xs">
                  {error}
                </div>
              )}

              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  disabled={guardando || carrito.length === 0}
                  onClick={() => handleSubmit(false)}
                  className="py-2.5 px-3 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center justify-center gap-1.5 transition active:scale-95 disabled:opacity-50 cursor-pointer"
                >
                  <Send className="w-3.5 h-3.5 text-amber-400" />
                  <span>Solo Cocina</span>
                </button>

                <button
                  type="button"
                  disabled={guardando || carrito.length === 0}
                  onClick={() => handleSubmit(true)}
                  className="py-2.5 px-3 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg flex items-center justify-center gap-1.5 transition active:scale-95 disabled:opacity-50 cursor-pointer"
                >
                  <DollarSign className="w-3.5 h-3.5" />
                  <span>Cobrar Ahora</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modal Táctil de Personalización para Mostrador / Caja */}
      <VariacionModal
        producto={productoParaVariacion}
        onClose={() => setProductoParaVariacion(null)}
        onAdd={handleAddCustom}
      />
    </div>
  )
}
