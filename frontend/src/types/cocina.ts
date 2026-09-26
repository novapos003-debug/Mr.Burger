export interface VariacionSnapshot {
  modificaciones?: string[]
  adiciones?: Array<{ id?: string; nombre: string; precio?: number }>
  notas?: string
  es_preparado?: boolean
  preparado_id?: number
  [key: string]: any
}

export type DetalleEstado = 'ENVIADO' | 'PREPARANDO' | 'LISTO' | 'CANCELADO'

export interface TicketDetalle {
  detalle_id: number
  producto_id: number
  producto_nombre: string
  cantidad: string | number
  variacion_snapshot?: VariacionSnapshot | null
  estado: DetalleEstado
  preparado_en?: string | null
  listo_en?: string | null
}

export interface TicketRonda {
  ronda: number
  detalles: TicketDetalle[]
}

export type CanalVenta = 'MESA' | 'MOSTRADOR' | 'DOMICILIO' | 'DIDI'

export interface Ticket {
  pedido_id: number
  consecutivo: number
  canal: CanalVenta
  mesa_numero?: number | null
  cliente?: string | null
  telefono?: string | null
  direccion?: string | null
  nota_interna?: string | null
  minutos_temporizador: number
  tiempo_excedido: boolean
  segundos_transcurridos: number
  rondas: TicketRonda[]
}

export type WebSocketStatus = 'conectado' | 'reconectando' | 'desconectado'

export interface WebSocketEvent {
  evento: string
  data: Record<string, any>
}
