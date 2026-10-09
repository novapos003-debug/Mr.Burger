export type MetodoPago =
  | 'EFECTIVO'
  | 'TARJETA'
  | 'TRANSFERENCIA'
  | 'VALE'
  | 'DIDI_TARJETA'
  | 'DIDI_EFECTIVO'

export interface PagoIn {
  metodo: MetodoPago
  monto: number
  recibido?: number | null
  didi_orden_id?: string | null
  vale_cliente_nombre?: string | null
  vale_cliente_cedula?: string | null
  vale_cliente_telefono?: string | null
}

export interface CobroIn {
  pagos: PagoIn[]
}

export interface PagoOut {
  id: number
  pedido_id: number
  metodo: MetodoPago
  monto: number
  recibido?: number | null
  cambio?: number | null
  didi_orden_id?: string | null
  estado: string
  usuario_id?: number | null
  pagado_en: string
  devuelto_en?: string | null
  motivo_devolucion?: string | null
}

export interface ValeOut {
  id: number
  pedido_id: number
  cliente_nombre: string
  cliente_cedula?: string | null
  cliente_telefono?: string | null
  monto: number
  estado: 'PENDIENTE' | 'COBRADO'
  cobrado_por?: number | null
  cobrado_en?: string | null
  creado_en: string
}

export interface CobroOut {
  pedido_id: number
  consecutivo: number
  total: number
  pagado: boolean
  pagos: PagoOut[]
  vales: ValeOut[]
}

export interface CierreOut {
  id: number
  usuario_id: number
  usuario_nombre?: string | null
  monto_inicial?: number
  abierto_en: string
  cerrado_en?: string | null
  total_pedidos: number
  total_venta_comida: number
  total_venta_bebida: number
  total_efectivo: number
  total_tarjeta: number
  total_transferencia: number
  total_vale: number
  cantidad_vales: number
  total_didi_tarjeta: number
  total_didi_efectivo: number
  total_entradas_caja: number
  total_salidas_caja: number
  cantidad_egresos: number
  total_devoluciones: number
  preparados_reutilizados: number
  preparados_descartados: number
  total_ventas: number
  total_efectivo_final: number
  total_por_cobrar: number
  notas?: string | null
}

export type TipoMovimiento = 'ENTRADA' | 'SALIDA'
export type CategoriaMovimiento =
  | 'PAGO_TURNO'
  | 'PRESTAMO'
  | 'ADELANTO'
  | 'PROVEEDOR'
  | 'DEVOLUCION'
  | 'COBRO_VALE'
  | 'CAMBIO_INICIAL'
  | 'GASTO_OPERATIVO'
  | 'OTRO'

export interface MovimientoCajaIn {
  tipo: TipoMovimiento
  categoria: CategoriaMovimiento
  valor: number
  descripcion: string
  concepto?: string | null
}

export interface MovimientoCajaOut {
  id: number
  usuario_id: number
  tipo: TipoMovimiento
  categoria: CategoriaMovimiento
  concepto: string
  descripcion: string
  valor: number
  pedido_id?: number | null
  vale_id?: number | null
  creado_en: string
}

export interface ConteoBilletesMonedas {
  b100k: number
  b50k: number
  b20k: number
  b10k: number
  b5k: number
  b2k: number
  m1000: number
  m500: number
  m200: number
  m100: number
  m50: number
  totalVouchersRedeban: number
}
