export interface TopProductoItem {
  producto_id: number
  nombre: string
  cantidad: number
  total: number
}

export interface AlertaStockItem {
  ingrediente_id: number
  nombre: string
  unidad_base: string
  stock_actual: number
  stock_minimo: number
  deficit: number
  costo_unitario: number
  costo_reabastecer: number
  proveedor_nombre?: string | null
}

export interface DashboardOut {
  fecha: string
  total_ventas: number
  total_pedidos: number
  ticket_promedio: number
  pedidos_por_estado: Record<string, number>
  ventas_por_canal: Record<string, number>
  ventas_por_tipo: Record<string, number>
  pagos_por_metodo: Record<string, number>
  entradas_caja: number
  salidas_caja: number
  devoluciones_caja: number
  vales_pendientes_monto: number
  vales_pendientes_cantidad: number
  preparados_disponibles_count: number
  top_productos: TopProductoItem[]
  alertas_stock: AlertaStockItem[]
}

export interface DesgloseDiaItem {
  fecha: string
  pedidos_count: number
  subtotal: number
  iva: number
  total: number
}

export interface ReporteVentasOut {
  desde: string
  hasta: string
  total_ventas: number
  total_pedidos: number
  ticket_promedio: number
  ventas_por_canal: Record<string, number>
  desglose_diario: DesgloseDiaItem[]
}

export interface DetalleCompraIn {
  ingrediente_id: number
  cantidad: number
  costo_unitario: number
}

export interface CompraIn {
  proveedor_id?: number | null
  descripcion?: string | null
  detalles: DetalleCompraIn[]
}

export interface DetalleCompraOut {
  id: number
  ingrediente_id: number
  ingrediente_nombre?: string | null
  cantidad: number
  costo_unitario: number
  costo_total: number
}

export interface CompraOut {
  id: number
  proveedor_id?: number | null
  proveedor_nombre?: string | null
  usuario_id: number
  usuario_nombre?: string | null
  descripcion?: string | null
  costo_total: number
  creado_en: string
  detalles: DetalleCompraOut[]
}

export interface HistorialAccionOut {
  id: number
  usuario_id?: number | null
  usuario_nombre?: string | null
  accion: string
  entidad?: string | null
  entidad_id?: number | null
  detalle?: string | null
  creado_en: string
}

export interface CategoriaInsumoItem {
  id: number
  nombre: string
  descripcion?: string | null
  activo: boolean
}

export interface IngredienteItem {
  id: number
  nombre: string
  categoria_insumo_id?: number | null
  categoria_insumo_nombre?: string | null
  tipo_articulo?: string | null
  unidad_base: string
  stock_actual: number
  stock_minimo: number
  stock_ideal?: number | null
  costo_unitario: number
  costo_proveedor?: string | null
  precio_venta?: number | null
  proveedor_id?: number | null
  proveedor_nombre?: string | null
  stock_bajo?: boolean
  activo?: boolean
}

export interface MovimientoInventarioItem {
  id: number
  ingrediente_id: number
  ingrediente_nombre?: string | null
  pedido_id?: number | null
  compra_id?: number | null
  usuario_id: number
  usuario_nombre?: string | null
  cantidad: number
  unidad?: string | null
  saldo_anterior?: number | null
  saldo_nuevo?: number | null
  costo_unitario_momento?: number | null
  tipo: string
  referencia?: string | null
  creado_en: string
}

export interface AnalisisCostoItem {
  costo_produccion: number
  precio_venta: number
  utilidad_bruta: number
  margen_porcentaje: number
}

export interface PreparadoAdminItem {
  id: number
  producto_id: number
  producto_nombre: string
  pedido_origen_id?: number | null
  consecutivo_origen?: number | null
  cantidad: number
  estado: string
  variacion_snapshot?: Record<string, any>
  minutos_espera: number
  creado_en: string
}

export interface DetalleRecetaItem {
  ingrediente_id: number
  ingrediente_nombre: string
  cantidad: number
  unidad: string
  unidad_base: string
  costo_unitario?: number | null
  costo_total?: number | null
  solo_llevar?: boolean
  precio_venta?: number | null
}

export interface DetalleRecetaInput {
  ingrediente_id: number
  cantidad: number
  unidad: string
  solo_llevar?: boolean
  precio_venta?: number | null
}

export interface UsuarioAdminItem {
  id: number
  nombre: string
  usuario: string
  rol_id: number
  rol: 'admin' | 'cajero' | 'mesero' | 'cocina' | string
  activo: boolean
  creado_en: string
}

export interface UsuarioCreateInput {
  nombre: string
  usuario: string
  password: string
  rol: 'admin' | 'cajero' | 'mesero' | 'cocina'
}
