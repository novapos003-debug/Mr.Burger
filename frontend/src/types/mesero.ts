export type EstadoMesa = 'DISPONIBLE' | 'EN_CURSO' | 'OCUPADA'
export type CanalVenta = 'MESA' | 'MOSTRADOR' | 'DOMICILIO' | 'DIDI'
export type EstadoPedido =
  | 'NUEVO'
  | 'ENVIADO_A_COCINA'
  | 'EN_PREPARACION'
  | 'FINALIZADO'
  | 'ENTREGADO'
  | 'PAGADO'
  | 'CERRADO'
  | 'CANCELADO'

export interface Mesa {
  id: number
  numero: number
  estado: EstadoMesa
  activo: boolean
}

export interface Categoria {
  id: number
  tipo_id: number
  nombre: string
  orden: number
  activo: boolean
}

export interface Producto {
  id: number
  categoria_id: number
  nombre: string
  descripcion?: string
  imagen_url?: string
  disponible: boolean
  activo: boolean
  precio?: number | null // null para mesero por regla
  es_cocina?: boolean
  ingredientes_receta?: string[]
  empaque_llevar_id?: number | null
  permite_adiciones?: boolean
  es_combo?: boolean
  componentes_combo?: Array<{
    id: number
    producto_hijo_id: number
    producto_hijo_nombre: string
    cantidad: number
    precio_unitario: number
  }>
}

export interface DetallePedido {
  id: number
  producto_id: number
  producto_nombre: string
  cantidad: number
  precio_unitario?: number | null
  variacion_snapshot?: Record<string, any> | null
  ronda: number
  estado: string
  preparado_en?: string | null
  listo_en?: string | null
  entregado_en?: string | null
  cancelado_en?: string | null
}

export type TipoConsumo = 'LOCAL' | 'LLEVAR'

export interface Pedido {
  id: number
  consecutivo: number
  fecha_dia: string
  canal: CanalVenta
  tipo_consumo?: TipoConsumo
  mesa_id?: number | null
  mesa_numero?: number | null
  estado: EstadoPedido
  cliente?: string | null
  telefono?: string | null
  direccion?: string | null
  nota_interna?: string | null
  didi_orden_id?: string | null
  creado_en: string
  enviado_en?: string | null
  finalizado_en?: string | null
  pagado_en?: string | null
  subtotal?: number | null
  iva?: number | null
  total?: number | null
  detalles: DetallePedido[]
}

export interface AdicionExtra {
  id: string
  nombre: string
  precio: number
}

export interface CartItem {
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

export interface PreparadoItem {
  id: number
  producto_id: number
  producto_nombre: string
  estado: string
  minutos_espera: number
  variacion_snapshot?: Record<string, any>
}
