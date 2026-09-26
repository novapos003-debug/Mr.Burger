import api from './client'
import type {
  CobroIn,
  CobroOut,
  CierreOut,
  ValeOut,
  MovimientoCajaIn,
  MovimientoCajaOut,
  PagoOut,
} from '../types/caja'
import type { Pedido } from '../types/mesero'

export const cobrarPedido = async (pedidoId: number, data: CobroIn): Promise<CobroOut> => {
  const res = await api.post<CobroOut>(`/caja/pedidos/${pedidoId}/cobrar`, data)
  return res.data
}

export const getTurnoActual = async (): Promise<CierreOut | null> => {
  const res = await api.get<CierreOut | null>('/caja/turno')
  return res.data
}

export const abrirTurno = async (montoInicial: number): Promise<CierreOut> => {
  const res = await api.post<CierreOut>('/caja/turno/abrir', { monto_inicial: montoInicial })
  return res.data
}

export const cerrarTurno = async (notas?: string): Promise<CierreOut> => {
  const res = await api.post<CierreOut>('/caja/turno/cerrar', { notas: notas || null })
  return res.data
}

export const getHistorialCierres = async (): Promise<CierreOut[]> => {
  const res = await api.get<CierreOut[]>('/caja/cierres')
  return res.data
}

export const getCierreDetalle = async (cierreId: number): Promise<CierreOut> => {
  const res = await api.get<CierreOut>(`/caja/cierres/${cierreId}`)
  return res.data
}

export const getVales = async (estado?: string): Promise<ValeOut[]> => {
  const params: Record<string, string> = {}
  if (estado) params.estado = estado
  const res = await api.get<ValeOut[]>('/caja/vales', { params })
  return res.data
}

export const cobrarVale = async (valeId: number, descripcion?: string): Promise<ValeOut> => {
  const res = await api.post<ValeOut>(`/caja/vales/${valeId}/cobrar`, { descripcion: descripcion || null })
  return res.data
}

export const getMovimientos = async (categoria?: string, tipo?: string): Promise<MovimientoCajaOut[]> => {
  const params: Record<string, string> = {}
  if (categoria) params.categoria = categoria
  if (tipo) params.tipo = tipo
  const res = await api.get<MovimientoCajaOut[]>('/caja/movimientos', { params })
  return res.data
}

export const crearMovimiento = async (data: MovimientoCajaIn): Promise<MovimientoCajaOut> => {
  const res = await api.post<MovimientoCajaOut>('/caja/movimientos', data)
  return res.data
}

export const devolverPago = async (pagoId: number, motivo: string): Promise<PagoOut> => {
  const res = await api.post<PagoOut>(`/caja/pagos/${pagoId}/devolver`, { motivo })
  return res.data
}

export const getPedidosActivos = async (tipo: string = 'activos', canal?: string): Promise<Pedido[]> => {
  const params: Record<string, string> = { tipo }
  if (canal) params.canal = canal
  const res = await api.get<Pedido[]>('/pedidos', { params })
  return res.data
}

export const crearPedidoCaja = async (data: any): Promise<Pedido> => {
  const res = await api.post<Pedido>('/pedidos', data)
  return res.data
}

export const enviarPedidoACocina = async (pedidoId: number): Promise<Pedido> => {
  const res = await api.post<Pedido>(`/pedidos/${pedidoId}/enviar-a-cocina`)
  return res.data
}
