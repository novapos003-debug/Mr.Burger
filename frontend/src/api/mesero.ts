import api from './client'
import type {
  Mesa,
  Categoria,
  Producto,
  Pedido,
  PreparadoItem,
} from '../types/mesero'

export const getMesasApi = async (): Promise<Mesa[]> => {
  const res = await api.get<Mesa[]>('/pedidos/mesas')
  return res.data
}

export const getCategoriasApi = async (): Promise<Categoria[]> => {
  const res = await api.get<Categoria[]>('/categorias')
  return res.data
}

export const getProductosApi = async (categoriaId?: number): Promise<Producto[]> => {
  const params = categoriaId ? { categoria_id: categoriaId } : {}
  const res = await api.get<Producto[]>('/productos', { params })
  return res.data
}

export const getPedidosActivosApi = async (): Promise<Pedido[]> => {
  const res = await api.get<Pedido[]>('/pedidos?tipo=activos')
  return res.data
}

export const getPedidoByIdApi = async (id: number): Promise<Pedido> => {
  const res = await api.get<Pedido>(`/pedidos/${id}`)
  return res.data
}

export interface CrearPedidoPayload {
  canal: string
  mesa_id?: number | null
  cliente?: string | null
  telefono?: string | null
  direccion?: string | null
  didi_orden_id?: string | null
  idempotency_key?: string
  lineas: {
    producto_id: number
    cantidad: number
    variacion_snapshot?: Record<string, any>
    preparado_id?: number
  }[]
}

export const crearPedidoApi = async (payload: CrearPedidoPayload): Promise<Pedido> => {
  const res = await api.post<Pedido>('/pedidos', payload)
  return res.data
}

export const enviarCocinaApi = async (pedidoId: number): Promise<Pedido> => {
  const res = await api.post<Pedido>(`/pedidos/${pedidoId}/enviar-a-cocina`)
  return res.data
}

export interface AgregarRondaPayload {
  ronda: number
  lineas: {
    producto_id: number
    cantidad: number
    variacion_snapshot?: Record<string, any>
    preparado_id?: number
  }[]
}

export const agregarRondaApi = async (
  pedidoId: number,
  payload: AgregarRondaPayload
): Promise<Pedido> => {
  const res = await api.post<Pedido>(`/pedidos/${pedidoId}/rondas`, payload)
  return res.data
}

export const getPreparadosDisponiblesApi = async (productoId?: number): Promise<PreparadoItem[]> => {
  const params: Record<string, any> = { estado: 'DISPONIBLE' }
  if (productoId) params.producto_id = productoId
  const res = await api.get<PreparadoItem[]>('/preparados', { params })
  return res.data
}
