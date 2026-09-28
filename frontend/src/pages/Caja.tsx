import React, { useState, useEffect, useCallback } from 'react'
import type { Pedido, DetallePedido } from '../types/mesero'
import type { CierreOut, CobroOut } from '../types/caja'
import {
  getTurnoActual,
  abrirTurno,
  getPedidosActivos,
  getVales,
} from '../api/caja'
import { useCocinaWebSocket } from '../hooks/useCocinaWebSocket'
import { CajaHeader } from '../components/caja/CajaHeader'
import { CobroModal } from '../components/caja/CobroModal'
import { AperturaTurnoModal } from '../components/caja/AperturaTurnoModal'
import { ArqueoCiegoModal } from '../components/caja/ArqueoCiegoModal'
import { MovimientosModal } from '../components/caja/MovimientosModal'
import { ValesModal } from '../components/caja/ValesModal'
import { NuevoPedidoModal } from '../components/caja/NuevoPedidoModal'
import { TirillaModal, type TipoTirilla } from '../components/common/TirillaModal'
import type { DatosReciboVenta, DatosReporteZ } from '../utils/printer'
import {
  DollarSign,
  Receipt,
  UtensilsCrossed,
  Store,
  Bike,
  ShoppingBag,
  Clock,
  CheckCircle2,
  Loader2,
  Lock,
  PlusCircle,
} from 'lucide-react'

interface DetalleVistaAgrupado {
  id: number
  cantidad: number
  producto_nombre: string
  estado: string
}

function agruparDetallesParaVista(detalles: DetallePedido[]): DetalleVistaAgrupado[] {
  const map = new Map<string, DetalleVistaAgrupado>()
  for (const d of detalles) {
    const key = `${d.producto_nombre}__${d.estado}`
    const existing = map.get(key)
    if (existing) {
      existing.cantidad += Number(d.cantidad) || 1
    } else {
      map.set(key, {
        id: d.id,
        cantidad: Number(d.cantidad) || 1,
        producto_nombre: d.producto_nombre,
        estado: d.estado,
      })
    }
  }
  return Array.from(map.values())
}

export const Caja: React.FC = () => {
  const [turno, setTurno] = useState<CierreOut | null>(null)
  const [pedidos, setPedidos] = useState<Pedido[]>([])
  const [valesPendientes, setValesPendientes] = useState<number>(0)
  const [filtroCanal, setFiltroCanal] = useState<string>('TODOS')
  const [loading, setLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Modales
  const [pedidoParaCobro, setPedidoParaCobro] = useState<Pedido | null>(null)
  const [isAperturaOpen, setIsAperturaOpen] = useState(false)
  const [isArqueoOpen, setIsArqueoOpen] = useState(false)
  const [isMovimientosOpen, setIsMovimientosOpen] = useState(false)
  const [isValesOpen, setIsValesOpen] = useState(false)
  const [isNuevoPedidoOpen, setIsNuevoPedidoOpen] = useState(false)
  const [tirillaConfig, setTirillaConfig] = useState<{
    isOpen: boolean
    tipo: TipoTirilla
    datosRecibo?: DatosReciboVenta
    datosReporteZ?: DatosReporteZ
  }>({
    isOpen: false,
    tipo: 'RECIBO'
  })

  // Cargar datos
  const cargarDatos = useCallback(async (showLoader = false) => {
    try {
      if (showLoader) setIsRefreshing(true)
      const [turnoRes, pedidosRes, valesRes] = await Promise.all([
        getTurnoActual(),
        getPedidosActivos('activos'),
        getVales('PENDIENTE'),
      ])
      setTurno(turnoRes)
      setPedidos(pedidosRes)
      setValesPendientes(valesRes.length)
    } catch (err) {
      console.error('Error cargando datos de caja:', err)
    } finally {
      setLoading(false)
      setIsRefreshing(false)
    }
  }, [])

  useEffect(() => {
    cargarDatos(false)
  }, [cargarDatos])

  // WebSocket para sincronización reactiva en vivo
  useCocinaWebSocket({
    onNewOrder: () => cargarDatos(false),
    onOrderUpdate: () => cargarDatos(false),
  })

  const handleAbrirTurno = async (montoInicial: number) => {
    const nuevoTurno = await abrirTurno(montoInicial)
    setTurno(nuevoTurno)
    cargarDatos(false)
  }

  const handleTurnoCerrado = (resultado: CierreOut) => {
    setTurno(null)
    cargarDatos(false)
    // Disparar Tirilla Reporte Z
    setTirillaConfig({
      isOpen: true,
      tipo: 'REPORTE_Z',
      datosReporteZ: {
        restaurante: 'MR. BURGER',
        turno_id: resultado.id,
        fecha_apertura: new Date(resultado.abierto_en).toLocaleString('es-CO'),
        fecha_cierre: new Date(resultado.cerrado_en || new Date()).toLocaleString('es-CO'),
        cajero: 'Caja Principal',
        monto_inicial: Number(resultado.total_entradas_caja || 0),
        total_ventas: Number(resultado.total_ventas),
        total_venta_comida: Number(resultado.total_venta_comida || 0),
        total_venta_bebida: Number(resultado.total_venta_bebida || 0),
        total_efectivo: Number(resultado.total_efectivo),
        total_tarjeta: Number(resultado.total_tarjeta),
        total_transferencia: Number(resultado.total_transferencia),
        total_didi_tarjeta: Number(resultado.total_didi_tarjeta),
        total_didi_efectivo: Number(resultado.total_didi_efectivo),
        total_vale: Number(resultado.total_vale),
        total_salidas_caja: Number(resultado.total_salidas_caja),
        total_entradas_caja: Number(resultado.total_entradas_caja),
        total_devoluciones: Number(resultado.total_devoluciones || 0),
        efectivo_esperado: Number(resultado.total_efectivo_final),
        preparados_reutilizados: resultado.preparados_reutilizados || 0,
        preparados_descartados: resultado.preparados_descartados || 0,
        notas: resultado.notas || undefined
      }
    })
  }

  const requerirTurno = (accion: () => void) => {
    if (!turno) {
      setIsAperturaOpen(true)
      return
    }
    accion()
  }

  const handleCobroExitoso = (resultado: CobroOut) => {
    // Generar recibo de venta si tenemos el pedido
    if (pedidoParaCobro) {
      const subtotalCalc = Number(pedidoParaCobro.subtotal) || Math.round(resultado.total / 1.19)
      const ivaCalc = Number(pedidoParaCobro.iva) || (resultado.total - subtotalCalc)
      const itemsMap = new Map<string, { cantidad: number; nombre: string; precio_unitario: number; total: number; variaciones?: string[] }>()
      for (const l of (pedidoParaCobro.detalles || [])) {
        const cant = Number(l.cantidad) || 1
        const precioUnit = Number(l.precio_unitario) || 0
        const variaciones = (l.variacion_snapshot?.modificaciones as string[]) || []
        const varKey = variaciones.slice().sort().join('|')
        const key = `${l.producto_nombre}__${precioUnit}__${varKey}`
        const existing = itemsMap.get(key)
        if (existing) {
          existing.cantidad += cant
          existing.total += Math.round(cant * precioUnit)
        } else {
          itemsMap.set(key, {
            cantidad: cant,
            nombre: l.producto_nombre,
            precio_unitario: precioUnit,
            total: Math.round(cant * precioUnit),
            variaciones: variaciones.length > 0 ? variaciones : undefined,
          })
        }
      }
      const items = Array.from(itemsMap.values())

      setTirillaConfig({
        isOpen: true,
        tipo: 'RECIBO',
        datosRecibo: {
          restaurante: 'MR. BURGER',
          lema: 'Simple por fuera. Inteligente por dentro.',
          nit: '901.234.567-8',
          ciudad: 'Cali, Valle del Cauca',
          telefono: '(602) 555-1234',
          direccion: 'Calle 5 # 66-12, Limonar',
          consecutivo: resultado.consecutivo,
          fecha: new Date().toLocaleString('es-CO'),
          canal: pedidoParaCobro.canal,
          mesa_numero: pedidoParaCobro.mesa_numero ?? pedidoParaCobro.mesa_id,
          cliente: pedidoParaCobro.cliente,
          direccion_entrega: pedidoParaCobro.direccion,
          items,
          subtotal: subtotalCalc,
          iva_porcentaje: 19,
          iva_valor: ivaCalc,
          total: resultado.total,
          pagos: resultado.pagos.map((p) => ({
            metodo: p.metodo,
            monto: Number(p.monto),
            recibido: p.recibido ? Number(p.recibido) : undefined,
            cambio: p.cambio ? Number(p.cambio) : undefined,
          })),
        },
      })
    }
    setPedidoParaCobro(null)
    cargarDatos(false)
  }

  const handleNuevoPedidoCreado = (pedidoId: number, abrirCobro: boolean) => {
    cargarDatos(false).then(() => {
      if (abrirCobro) {
        // Encontrar pedido recién creado
        getPedidosActivos('activos').then((lista) => {
          const encontrado = lista.find((p) => p.id === pedidoId)
          if (encontrado) {
            requerirTurno(() => setPedidoParaCobro(encontrado))
          }
        })
      }
    })
  }

  // Filtrado de pedidos
  const pedidosFiltrados = pedidos.filter((p) => {
    if (filtroCanal === 'TODOS') return true
    if (filtroCanal === 'MESA') return p.canal === 'MESA'
    if (filtroCanal === 'MOSTRADOR') return p.canal === 'MOSTRADOR'
    if (filtroCanal === 'DOMICILIO') return p.canal === 'DOMICILIO'
    if (filtroCanal === 'DIDI') return p.canal === 'DIDI'
    return true
  })

  // Conteo por canal
  const countMesas = pedidos.filter((p) => p.canal === 'MESA').length
  const countMostrador = pedidos.filter((p) => p.canal === 'MOSTRADOR').length
  const countDomicilio = pedidos.filter((p) => p.canal === 'DOMICILIO').length
  const countDidi = pedidos.filter((p) => p.canal === 'DIDI').length

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col select-none">
      {/* Cabecera Principal de Caja */}
      <CajaHeader
        turno={turno}
        onAbrirTurnoClick={() => setIsAperturaOpen(true)}
        onCerrarTurnoClick={() => setIsArqueoOpen(true)}
        onMovimientosClick={() => requerirTurno(() => setIsMovimientosOpen(true))}
        onValesClick={() => setIsValesOpen(true)}
        onNuevoPedidoClick={() => requerirTurno(() => setIsNuevoPedidoOpen(true))}
        onRefresh={() => cargarDatos(true)}
        isRefreshing={isRefreshing}
        totalValesPendientes={valesPendientes}
      />

      {/* Alerta si la caja está cerrada */}
      {!loading && !turno && (
        <div className="bg-gradient-to-r from-amber-950/60 to-slate-900 border-b border-amber-800/40 p-4 text-center">
          <div className="max-w-xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 text-amber-300 text-xs text-left">
              <Lock className="w-5 h-5 shrink-0 text-amber-400" />
              <span>
                <strong>Caja Cerrada:</strong> Para cobrar pedidos o registrar movimientos, abre el turno de caja con la base de efectivo inicial.
              </span>
            </div>
            <button
              onClick={() => setIsAperturaOpen(true)}
              className="px-4 py-2 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 text-white shadow transition cursor-pointer shrink-0"
            >
              Abrir Turno Ahora
            </button>
          </div>
        </div>
      )}

      {/* Barra de Filtros de Canal */}
      <div className="bg-slate-900/60 border-b border-slate-800 px-4 py-2.5 flex items-center justify-between gap-2 overflow-x-auto no-scrollbar">
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setFiltroCanal('TODOS')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
              filtroCanal === 'TODOS'
                ? 'bg-emerald-600 text-white shadow'
                : 'bg-slate-800/60 text-slate-400 hover:text-white'
            }`}
          >
            Todas ({pedidos.length})
          </button>
          <button
            onClick={() => setFiltroCanal('MESA')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
              filtroCanal === 'MESA'
                ? 'bg-indigo-600 text-white shadow'
                : 'bg-slate-800/60 text-slate-400 hover:text-white'
            }`}
          >
            <UtensilsCrossed className="w-3.5 h-3.5" />
            <span>Mesas ({countMesas})</span>
          </button>
          <button
            onClick={() => setFiltroCanal('MOSTRADOR')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
              filtroCanal === 'MOSTRADOR'
                ? 'bg-sky-600 text-white shadow'
                : 'bg-slate-800/60 text-slate-400 hover:text-white'
            }`}
          >
            <Store className="w-3.5 h-3.5" />
            <span>Mostrador ({countMostrador})</span>
          </button>
          <button
            onClick={() => setFiltroCanal('DOMICILIO')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
              filtroCanal === 'DOMICILIO'
                ? 'bg-purple-600 text-white shadow'
                : 'bg-slate-800/60 text-slate-400 hover:text-white'
            }`}
          >
            <Bike className="w-3.5 h-3.5" />
            <span>Domicilios ({countDomicilio})</span>
          </button>
          <button
            onClick={() => setFiltroCanal('DIDI')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
              filtroCanal === 'DIDI'
                ? 'bg-orange-600 text-white shadow'
                : 'bg-slate-800/60 text-slate-400 hover:text-white'
            }`}
          >
            <ShoppingBag className="w-3.5 h-3.5" />
            <span>DiDi Food ({countDidi})</span>
          </button>
        </div>

        <button
          onClick={() => requerirTurno(() => setIsNuevoPedidoOpen(true))}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition cursor-pointer shrink-0"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Nueva Orden</span>
        </button>
      </div>

      {/* Contenido Principal: Tarjetas de Pedidos en Caja */}
      <main className="flex-1 p-4 max-w-7xl mx-auto w-full">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-10 h-10 text-emerald-500 animate-spin mb-3" />
            <span className="text-slate-400 font-bold text-sm">Cargando pedidos de caja...</span>
          </div>
        ) : pedidosFiltrados.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center px-4">
            <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-emerald-400 mb-4 shadow-xl">
              <Receipt className="w-8 h-8 text-emerald-400" />
            </div>
            <h2 className="text-xl font-bold text-white mb-1">Sin Pedidos Pendientes</h2>
            <p className="text-slate-400 text-xs max-w-md mb-5 leading-relaxed">
              No hay órdenes activas en el filtro seleccionado. Puedes crear un nuevo pedido de mostrador o esperar a que los meseros envíen órdenes desde las mesas.
            </p>
            <button
              onClick={() => requerirTurno(() => setIsNuevoPedidoOpen(true))}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-black bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-md transition cursor-pointer"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Tomar Pedido en Mostrador / Domicilio</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 items-start">
            {pedidosFiltrados.map((pedido) => {
              const total = Number(pedido.total || 0)
              const yaPagado = pedido.pagado_en !== null

              const getCanalBadge = () => {
                switch (pedido.canal) {
                  case 'MESA':
                    return (
                      <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-black bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                        <UtensilsCrossed className="w-3.5 h-3.5" />
                        MESA {pedido.mesa_numero}
                      </span>
                    )
                  case 'MOSTRADOR':
                    return (
                      <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-black bg-sky-500/20 text-sky-300 border border-sky-500/40">
                        <Store className="w-3.5 h-3.5" />
                        MOSTRADOR
                      </span>
                    )
                  case 'DOMICILIO':
                    return (
                      <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-black bg-purple-500/20 text-purple-300 border border-purple-500/40">
                        <Bike className="w-3.5 h-3.5" />
                        DOMICILIO
                      </span>
                    )
                  case 'DIDI':
                    return (
                      <span className="flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-black bg-orange-500/20 text-orange-300 border border-orange-500/40">
                        <ShoppingBag className="w-3.5 h-3.5" />
                        DIDI
                      </span>
                    )
                }
              }

              return (
                <div
                  key={pedido.id}
                  className={`bg-slate-900 rounded-2xl border transition-all duration-200 overflow-hidden shadow-xl flex flex-col justify-between ${
                    yaPagado
                      ? 'border-emerald-800/40 bg-slate-900/60'
                      : 'border-slate-800 hover:border-emerald-500/50'
                  }`}
                >
                  {/* Encabezado Pedido */}
                  <div className="p-3.5 border-b border-slate-800/80 bg-slate-800/40 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-black text-white font-mono">
                        #{pedido.consecutivo}
                      </span>
                      {getCanalBadge()}
                    </div>

                    {yaPagado ? (
                      <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-black bg-emerald-950 text-emerald-400 border border-emerald-700">
                        <CheckCircle2 className="w-3 h-3" />
                        PAGADO
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-amber-950/70 text-amber-300 border border-amber-800">
                        <Clock className="w-3 h-3" />
                        POR COBRAR
                      </span>
                    )}
                  </div>

                  {/* Datos del Cliente si existen */}
                  {(pedido.cliente || pedido.direccion || pedido.didi_orden_id) && (
                    <div className="px-3.5 py-1.5 bg-slate-950/70 border-b border-slate-800/60 text-[11px] text-slate-300 space-y-0.5">
                      {pedido.cliente && (
                        <div>Cliente: <strong>{pedido.cliente}</strong></div>
                      )}
                      {pedido.direccion && (
                        <div className="truncate text-slate-400">Dir: {pedido.direccion}</div>
                      )}
                      {pedido.didi_orden_id && (
                        <div className="text-orange-400 font-mono font-semibold">Orden: {pedido.didi_orden_id}</div>
                      )}
                    </div>
                  )}

                  {/* Lista de Ítems */}
                  <div className="p-3.5 space-y-1.5 flex-1 max-h-[180px] overflow-y-auto">
                    {agruparDetallesParaVista(pedido.detalles || []).map((d) => (
                      <div key={d.id} className="flex items-center justify-between text-xs">
                        <span className="text-slate-200">
                          <strong className="text-amber-400 mr-1">{Number(d.cantidad)}x</strong>
                          {d.producto_nombre}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                          {d.estado}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Total y Botón de Cobro */}
                  <div className="p-3.5 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between gap-2">
                    <div>
                      <span className="text-[10px] text-slate-400 block uppercase font-bold">Total a Pagar</span>
                      <span className="text-xl font-black text-emerald-400 font-mono">
                        ${total.toLocaleString('es-CO')}
                      </span>
                    </div>

                    {!yaPagado ? (
                      <button
                        onClick={() => requerirTurno(() => setPedidoParaCobro(pedido))}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-xl font-black text-xs bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white shadow-lg shadow-emerald-950/50 transition cursor-pointer"
                      >
                        <DollarSign className="w-4 h-4" />
                        <span>Cobrar</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => setPedidoParaCobro(pedido)}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-xl font-semibold text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition cursor-pointer"
                        title="Ver detalles de los pagos y reimprimir"
                      >
                        <Receipt className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Ver Pago</span>
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </main>

      {/* Modales del Módulo de Caja */}
      <AperturaTurnoModal
        isOpen={isAperturaOpen}
        onClose={() => setIsAperturaOpen(false)}
        onConfirm={handleAbrirTurno}
      />

      <ArqueoCiegoModal
        isOpen={isArqueoOpen}
        turno={turno}
        onClose={() => setIsArqueoOpen(false)}
        onTurnoCerrado={handleTurnoCerrado}
      />

      <CobroModal
        isOpen={pedidoParaCobro !== null}
        pedido={pedidoParaCobro}
        onClose={() => setPedidoParaCobro(null)}
        onSuccess={handleCobroExitoso}
      />

      <MovimientosModal
        isOpen={isMovimientosOpen}
        onClose={() => setIsMovimientosOpen(false)}
      />

      <ValesModal
        isOpen={isValesOpen}
        onClose={() => setIsValesOpen(false)}
        onValeCobrado={() => cargarDatos(false)}
      />

      <NuevoPedidoModal
        isOpen={isNuevoPedidoOpen}
        onClose={() => setIsNuevoPedidoOpen(false)}
        onPedidoCreado={handleNuevoPedidoCreado}
      />

      <TirillaModal
        isOpen={tirillaConfig.isOpen}
        onClose={() => setTirillaConfig((prev) => ({ ...prev, isOpen: false }))}
        tipo={tirillaConfig.tipo}
        datosRecibo={tirillaConfig.datosRecibo}
        datosReporteZ={tirillaConfig.datosReporteZ}
      />
    </div>
  )
}
