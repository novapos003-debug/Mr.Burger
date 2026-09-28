import React, { useState, useEffect, useCallback } from 'react'
import { Navbar } from '../components/Navbar'
import { MesaSelector } from '../components/mesero/MesaSelector'
import { CatalogoMesero } from '../components/mesero/CatalogoMesero'
import { VariacionModal } from '../components/mesero/VariacionModal'
import { ComandaSidebar } from '../components/mesero/ComandaSidebar'
import {
  getMesasApi,
  getCategoriasApi,
  getProductosApi,
  getPedidosActivosApi,
  crearPedidoApi,
  enviarCocinaApi,
  agregarRondaApi,
} from '../api/mesero'
import type {
  Mesa,
  Categoria,
  Producto,
  Pedido,
  CartItem,
  AdicionExtra,
} from '../types/mesero'
import {
  getPendingOrders,
  savePendingOrder,
  syncPendingOrders,
} from '../utils/offlineQueue'
import {
  CheckCircle2,
  AlertCircle,
  ShoppingBag,
  X,
  Layers,
  Send,
  WifiOff,
  RefreshCw,
} from 'lucide-react'

export const Mesero: React.FC = () => {
  // Datos del backend
  const [mesas, setMesas] = useState<Mesa[]>([])
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [productos, setProductos] = useState<Producto[]>([])
  const [pedidosActivos, setPedidosActivos] = useState<Pedido[]>([])

  // Estado de la mesa y comanda (el mesero solo atiende MESAS)
  const [mesaSeleccionada, setMesaSeleccionada] = useState<Mesa | null>(null)
  const [cartItems, setCartItems] = useState<CartItem[]>([])
  const [modalProducto, setModalProducto] = useState<Producto | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Feedback y drawer móvil
  const [successBanner, setSuccessBanner] = useState<string | null>(null)
  const [errorBanner, setErrorBanner] = useState<string | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [offlineCount, setOfflineCount] = useState<number>(() => getPendingOrders().length)

  // Cargar datos
  const cargarDatos = useCallback(async () => {
    try {
      const [mRes, cRes, pRes, actRes] = await Promise.allSettled([
        getMesasApi(),
        getCategoriasApi(),
        getProductosApi(),
        getPedidosActivosApi(),
      ])

      let menuOk = true
      if (mRes.status === 'fulfilled') setMesas(mRes.value)
      else menuOk = false

      if (cRes.status === 'fulfilled') setCategorias(cRes.value)
      else menuOk = false

      if (pRes.status === 'fulfilled') setProductos(pRes.value)
      else menuOk = false

      if (actRes.status === 'fulfilled') setPedidosActivos(actRes.value)

      if (!menuOk) {
        setErrorBanner('Error al sincronizar mesas y menú con el servidor local')
      } else {
        setErrorBanner(null)
      }
    } catch {
      setErrorBanner('Error al sincronizar mesas y menú con el servidor local')
    }
  }, [])

  useEffect(() => {
    cargarDatos()
    // Polling ligero cada 8s para sincronizar estado de mesas
    const interval = setInterval(cargarDatos, 8000)
    return () => clearInterval(interval)
  }, [cargarDatos])

  // Sincronización automática de pedidos pendientes por microcortes Wi-Fi
  useEffect(() => {
    const handleSync = async () => {
      const res = await syncPendingOrders((_, msg) => {
        setSuccessBanner(`¡Sincronizado! ${msg}`)
        cargarDatos()
      })
      setOfflineCount(res.pendientes)
    }

    window.addEventListener('online', handleSync)
    const interval = setInterval(handleSync, 5000)

    return () => {
      window.removeEventListener('online', handleSync)
      clearInterval(interval)
    }
  }, [cargarDatos])

  // Pedido activo de la mesa seleccionada (si existe)
  const pedidoActivo = mesaSeleccionada
    ? pedidosActivos.find(
        (p) =>
          p.mesa_id === mesaSeleccionada.id &&
          !['PAGADO', 'CERRADO', 'CANCELADO'].includes(p.estado)
      ) || null
    : null

  // Manejar selección de mesa
  const handleSelectMesa = (m: Mesa) => {
    setMesaSeleccionada(m)
  }

  // Agregar producto rápido desde el catálogo (+1)
  const handleQuickAdd = (producto: Producto) => {
    setCartItems((prev) => {
      // Si el producto ya existe en el carrito sin personalizaciones, incrementar cantidad
      const existingIndex = prev.findIndex(
        (item) =>
          item.producto.id === producto.id &&
          (!item.variacion || (
            !item.variacion.notas &&
            (!item.variacion.modificaciones || item.variacion.modificaciones.length === 0) &&
            (!item.variacion.adiciones || item.variacion.adiciones.length === 0) &&
            !item.variacion.preparado_id
          ))
      )
      if (existingIndex >= 0) {
        return prev.map((item, idx) =>
          idx === existingIndex
            ? { ...item, cantidad: item.cantidad + 1 }
            : item
        )
      }
      const newItem: CartItem = {
        uid: `${producto.id}-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
        producto,
        cantidad: 1,
        precio_unitario: Number(producto.precio || 0),
        variacion: {},
      }
      return [...prev, newItem]
    })
  }

  // Agregar producto desde modal con personalización y adiciones
  const handleAddCustom = (
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
  ) => {
    const newItem: CartItem = {
      uid: `${producto.id}-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
      producto,
      cantidad,
      precio_unitario: precioUnitarioCalculado,
      variacion,
    }
    setCartItems((prev) => [...prev, newItem])
  }

  // Modificar cantidad
  const handleUpdateCantidad = (uid: string, delta: number) => {
    setCartItems((prev) =>
      prev
        .map((item) => {
          if (item.uid === uid) {
            const newQty = item.cantidad + delta
            return newQty > 0 ? { ...item, cantidad: newQty } : null
          }
          return item
        })
        .filter(Boolean) as CartItem[]
    )
  }

  // Eliminar ítem
  const handleRemoveItem = (uid: string) => {
    setCartItems((prev) => prev.filter((i) => i.uid !== uid))
  }

  // Vaciar carrito
  const handleClearCart = () => {
    setCartItems([])
  }

  // Enviar a cocina
  const handleSubmitComanda = async () => {
    setErrorBanner(null)
    setSuccessBanner(null)

    if (!mesaSeleccionada) {
      setErrorBanner('Por favor toca una mesa (1-9) arriba antes de enviar a cocina.')
      return
    }

    if (cartItems.length === 0) return

    setSubmitting(true)
    const idempotencyKey = `ord-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`

    // Consolidar ítems idénticos para que no se dupliquen las líneas en cocina ni caja
    const lineasConsolidadas = (() => {
      const map = new Map<string, { producto_id: number; cantidad: number; variacion_snapshot?: any; preparado_id?: number }>()
      for (const item of cartItems) {
        const key = `${item.producto.id}__${JSON.stringify(item.variacion || {})}__${item.variacion?.preparado_id || ''}`
        const existing = map.get(key)
        if (existing) {
          existing.cantidad += item.cantidad
        } else {
          map.set(key, {
            producto_id: item.producto.id,
            cantidad: item.cantidad,
            variacion_snapshot: item.variacion,
            preparado_id: item.variacion?.preparado_id,
          })
        }
      }
      return Array.from(map.values())
    })()

    try {
      if (pedidoActivo) {
        // AGREGAR NUEVA RONDA A LA MESA
        const nextRonda = Math.max(...pedidoActivo.detalles.map((d) => d.ronda), 1) + 1
        await agregarRondaApi(pedidoActivo.id, {
          ronda: nextRonda,
          lineas: lineasConsolidadas,
        })

        setSuccessBanner(
          `¡Ronda #${nextRonda} enviada a cocina para Mesa ${mesaSeleccionada.numero}!`
        )
      } else {
        // CREAR NUEVO PEDIDO EN LA MESA Y ENVIAR A COCINA
        const payloadNuevo = {
          canal: 'MESA',
          mesa_id: mesaSeleccionada.id,
          idempotency_key: idempotencyKey,
          lineas: lineasConsolidadas,
        }
        const nuevo = await crearPedidoApi(payloadNuevo)

        // Enviar a cocina
        await enviarCocinaApi(nuevo.id)

        setSuccessBanner(
          `¡Comanda enviada a cocina para Mesa #${mesaSeleccionada.numero}! (Orden #${nuevo.consecutivo})`
        )
      }

      // Limpiar comanda y cerrar drawer
      setCartItems([])
      setDrawerOpen(false)

      // Recargar mesas
      await cargarDatos()
    } catch (err: any) {
      if (!err.response || err.code === 'ERR_NETWORK') {
        if (pedidoActivo) {
          const nextRonda = Math.max(...pedidoActivo.detalles.map((d) => d.ronda), 1) + 1
          savePendingOrder({
            tipo: 'RONDA',
            pedidoId: pedidoActivo.id,
            mesaNumero: mesaSeleccionada.numero,
            payloadRonda: {
              ronda: nextRonda,
              lineas: cartItems.map((item) => ({
                producto_id: item.producto.id,
                cantidad: item.cantidad,
                variacion_snapshot: item.variacion,
                preparado_id: item.variacion.preparado_id,
              })),
            },
          })
        } else {
          const orderFallback = savePendingOrder({
            tipo: 'NUEVO_PEDIDO',
            mesaNumero: mesaSeleccionada.numero,
            payloadNuevo: {
              canal: 'MESA',
              mesa_id: mesaSeleccionada.id,
              idempotency_key: idempotencyKey,
              lineas: cartItems.map((item) => ({
                producto_id: item.producto.id,
                cantidad: item.cantidad,
                variacion_snapshot: item.variacion,
                preparado_id: item.variacion.preparado_id,
              })),
            },
          })
          orderFallback.id = idempotencyKey
          const queueRaw = localStorage.getItem('pos_mesero_offline_queue')
          if (queueRaw) {
             const queue = JSON.parse(queueRaw)
             const last = queue[queue.length - 1]
             if (last) {
                last.id = idempotencyKey
                localStorage.setItem('pos_mesero_offline_queue', JSON.stringify(queue))
             }
          }
        }

        setOfflineCount(getPendingOrders().length)
        setSuccessBanner(
          `📶 Wi-Fi inestable: Comanda de Mesa #${mesaSeleccionada.numero} guardada en tu teléfono. Se enviará sola a cocina al restablecer la señal.`
        )
        setCartItems([])
        setDrawerOpen(false)
      } else {
        setErrorBanner(
          err.response?.data?.detail || 'Error al enviar la comanda a la cocina'
        )
      }
    } finally {
      setSubmitting(false)
    }
  }

  const totalItemsCount = cartItems.reduce((acc, i) => acc + i.cantidad, 0)
  const totalNuevosItems = cartItems.reduce((acc, i) => acc + i.precio_unitario * i.cantidad, 0)
  const isRonda = !!pedidoActivo && !['PAGADO', 'CERRADO', 'CANCELADO'].includes(pedidoActivo.estado)

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col selection:bg-orange-500 selection:text-white">
      <Navbar title="Mesero Móvil • Salón Mr. Burger" />

      {/* Banner de Pedidos Offline pendientes por reconexión Wi-Fi */}
      {offlineCount > 0 && (
        <div className="bg-amber-950/90 border-b border-amber-700/80 px-4 py-2 flex items-center justify-between text-amber-200 text-xs font-semibold z-20 sticky top-[53px]">
          <div className="flex items-center gap-2">
            <WifiOff className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              {offlineCount} {offlineCount === 1 ? 'pedido guardado' : 'pedidos guardados'} en el teléfono esperando reconexión Wi-Fi...
            </span>
          </div>
          <button
            onClick={async () => {
              const res = await syncPendingOrders((_, msg) => {
                setSuccessBanner(msg)
                cargarDatos()
              })
              setOfflineCount(res.pendientes)
            }}
            className="flex items-center gap-1 bg-amber-800 hover:bg-amber-700 text-white px-2 py-1 rounded text-[11px] cursor-pointer"
          >
            <RefreshCw className="w-3 h-3 animate-spin" />
            Reintentar
          </button>
        </div>
      )}

      {/* Banners Flotantes de Éxito / Error */}
      {successBanner && (
        <div className="fixed top-14 left-1/2 transform -translate-x-1/2 z-50 w-11/12 max-w-md p-3 bg-emerald-950 border-2 border-emerald-500 text-emerald-100 rounded-2xl shadow-2xl flex items-center justify-between gap-2 animate-bounce">
          <div className="flex items-center gap-2 text-xs font-bold">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{successBanner}</span>
          </div>
          <button onClick={() => setSuccessBanner(null)} className="text-emerald-400 hover:text-white p-1">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {errorBanner && (
        <div className="fixed top-14 left-1/2 transform -translate-x-1/2 z-50 w-11/12 max-w-md p-3 bg-red-950 border-2 border-red-500 text-red-100 rounded-2xl shadow-2xl flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-xs font-bold">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{errorBanner}</span>
          </div>
          <button onClick={() => setErrorBanner(null)} className="text-red-400 hover:text-white p-1">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Contenido Principal */}
      <main className="flex-1 flex flex-col lg:flex-row p-2 sm:p-3 gap-2 sm:gap-3 max-w-[1600px] mx-auto w-full overflow-hidden pb-16 lg:pb-2">
        {/* Columna Izquierda: Mesas 1 a 9 + Catálogo */}
        <div className="flex-1 flex flex-col min-h-0">
          {/* Selector Compacto de Mesas 1 a 9 (Ocupa mínimo espacio vertical) */}
          <div className="mb-2 bg-slate-900/80 p-2 rounded-2xl border border-slate-800/80">
            <MesaSelector
              mesas={mesas}
              pedidosActivos={pedidosActivos}
              mesaSeleccionada={mesaSeleccionada}
              onSelectMesa={handleSelectMesa}
            />
          </div>

          {/* Catálogo de Productos con Filtros Táctiles y Precios */}
          <div className="flex-1 min-h-0 flex flex-col bg-slate-950/40 rounded-2xl">
            <CatalogoMesero
              categorias={categorias}
              productos={productos}
              onSelectProducto={(p) => setModalProducto(p)}
              onQuickAdd={handleQuickAdd}
            />
          </div>
        </div>

        {/* Columna Derecha en Pantallas Grandes (Tablet horizontal / Desktop) */}
        <div className="hidden lg:flex w-84 xl:w-96 flex-col shrink-0">
          <ComandaSidebar
            items={cartItems}
            mesa={mesaSeleccionada}
            pedidoActivo={pedidoActivo}
            onUpdateCantidad={handleUpdateCantidad}
            onRemoveItem={handleRemoveItem}
            onClearCart={handleClearCart}
            onSubmit={handleSubmitComanda}
            submitting={submitting}
          />
        </div>

        {/* Barra Flotante Inferior para Móviles (Super Ágil y Ergonómica) */}
        <div className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-900/95 backdrop-blur-md border-t border-slate-800 p-2.5 px-3 flex items-center justify-between shadow-2xl">
          <div
            onClick={() => setDrawerOpen(true)}
            className="flex-1 flex items-center gap-2.5 cursor-pointer select-none mr-2"
          >
            <div className="w-10 h-10 rounded-xl bg-orange-600 flex items-center justify-center text-white font-black shadow-lg shadow-orange-600/40 shrink-0">
              {totalItemsCount > 0 ? (
                <span className="text-sm">{totalItemsCount}</span>
              ) : (
                <ShoppingBag className="w-5 h-5" />
              )}
            </div>

            <div className="overflow-hidden">
              <p className="text-xs font-black text-white truncate leading-tight">
                {mesaSeleccionada ? `Mesa #${mesaSeleccionada.numero}` : 'Sin mesa elegida'}
              </p>
              <p className="text-[11px] font-mono font-bold text-emerald-400">
                {totalItemsCount > 0
                  ? `$${totalNuevosItems.toLocaleString('es-CO')}`
                  : isRonda
                  ? 'Cuenta en curso'
                  : 'Toca para ver'}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            className="py-2.5 px-4 bg-gradient-to-r from-orange-600 to-amber-600 active:scale-95 text-white font-black text-xs rounded-xl shadow-lg shadow-orange-600/30 flex items-center gap-1.5 cursor-pointer shrink-0"
          >
            {isRonda ? (
              <>
                <Layers className="w-3.5 h-3.5" />
                <span>Ronda / Ver</span>
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>Ver Comanda</span>
              </>
            )}
          </button>
        </div>

        {/* Drawer Deslizable Inferior / Lateral en Móviles */}
        {drawerOpen && (
          <div className="lg:hidden fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex flex-col justify-end animate-fade-in">
            <div className="w-full bg-slate-900 rounded-t-3xl max-h-[85vh] p-3 sm:p-4 flex flex-col border-t border-slate-700 shadow-2xl">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                <span className="font-black text-sm text-white">
                  {mesaSeleccionada
                    ? `Comanda Mesa #${mesaSeleccionada.numero}`
                    : 'Comanda de Salón'}
                </span>
                <button
                  onClick={() => setDrawerOpen(false)}
                  className="p-1.5 rounded-full bg-slate-800 text-slate-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="flex-1 min-h-0 overflow-y-auto">
                <ComandaSidebar
                  items={cartItems}
                  mesa={mesaSeleccionada}
                  pedidoActivo={pedidoActivo}
                  onUpdateCantidad={handleUpdateCantidad}
                  onRemoveItem={handleRemoveItem}
                  onClearCart={handleClearCart}
                  onSubmit={handleSubmitComanda}
                  submitting={submitting}
                />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Modal Táctil de Personalización y Adiciones */}
      <VariacionModal
        producto={modalProducto}
        onClose={() => setModalProducto(null)}
        onAdd={handleAddCustom}
      />
    </div>
  )
}
