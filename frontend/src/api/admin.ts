import api from './client'
import type { Producto, AdicionExtra } from '../types/mesero'
import type {
  DashboardOut,
  ReporteVentasOut,
  AlertaStockItem,
  CompraIn,
  CompraOut,
  HistorialAccionOut,
  IngredienteItem,
  CategoriaInsumoItem,
  MovimientoInventarioItem,
  AnalisisCostoItem,
  PreparadoAdminItem,
  DetalleRecetaItem,
  DetalleRecetaInput,
  UsuarioAdminItem,
  UsuarioCreateInput,
  ResetSistemaInput,
  ResetResumenOut,
} from '../types/admin'

export const getDashboardApi = async (fecha?: string): Promise<DashboardOut> => {
  const params = fecha ? { fecha } : {}
  const res = await api.get<DashboardOut>('/admin/dashboard', { params })
  return res.data
}

export const getReporteVentasApi = async (
  desde: string,
  hasta: string,
  canal?: string
): Promise<ReporteVentasOut> => {
  const params: any = { desde, hasta }
  if (canal && canal !== 'TODOS') params.canal = canal
  const res = await api.get<ReporteVentasOut>('/admin/reportes/ventas', { params })
  return res.data
}

export const getStockCriticoApi = async (): Promise<AlertaStockItem[]> => {
  const res = await api.get<AlertaStockItem[]>('/admin/stock-critico')
  return res.data
}

export const getComprasApi = async (limit = 50, offset = 0): Promise<CompraOut[]> => {
  const res = await api.get<CompraOut[]>('/admin/compras', { params: { limit, offset } })
  return res.data
}

export const crearCompraApi = async (data: CompraIn): Promise<CompraOut> => {
  const res = await api.post<CompraOut>('/admin/compras', data)
  return res.data
}

export const getAuditoriaApi = async (params?: {
  usuario_id?: number
  accion?: string
  entidad?: string
  limit?: number
  offset?: number
}): Promise<HistorialAccionOut[]> => {
  const res = await api.get<HistorialAccionOut[]>('/admin/auditoria', { params })
  return res.data
}

export const getCategoriasInsumoApi = async (): Promise<CategoriaInsumoItem[]> => {
  const res = await api.get<CategoriaInsumoItem[]>('/ingredientes/categorias')
  return res.data
}

export const crearCategoriaInsumoApi = async (data: { nombre: string; descripcion?: string }): Promise<CategoriaInsumoItem> => {
  const res = await api.post<CategoriaInsumoItem>('/ingredientes/categorias', data)
  return res.data
}

export const getIngredientesApi = async (categoriaInsumoId?: number): Promise<IngredienteItem[]> => {
  const params = categoriaInsumoId ? { categoria_insumo_id: categoriaInsumoId } : {}
  const res = await api.get<IngredienteItem[]>('/ingredientes', { params })
  return res.data
}

export const crearIngredienteApi = async (data: {
  nombre: string
  categoria_insumo_id?: number | null
  tipo_articulo?: string | null
  unidad_base: string
  costo_unitario?: number
  precio_venta?: number
  stock_actual?: number
  stock_minimo?: number
}): Promise<IngredienteItem> => {
  const res = await api.post<IngredienteItem>('/ingredientes', data)
  return res.data
}

export const actualizarIngredienteApi = async (
  id: number,
  data: Partial<IngredienteItem>
): Promise<IngredienteItem> => {
  const res = await api.put<IngredienteItem>(`/ingredientes/${id}`, data)
  return res.data
}

export const getMovimientosIngredienteApi = async (
  ingredienteId: number,
  limit = 50,
  offset = 0
): Promise<MovimientoInventarioItem[]> => {
  const res = await api.get<MovimientoInventarioItem[]>(`/ingredientes/${ingredienteId}/movimientos`, {
    params: { limit, offset },
  })
  return res.data
}

export const getRecetaProductoApi = async (productoId: number): Promise<DetalleRecetaItem[]> => {
  const res = await api.get<DetalleRecetaItem[]>(`/ingredientes/productos/${productoId}/receta`)
  return res.data
}

export const guardarRecetaProductoApi = async (
  productoId: number,
  lineas: DetalleRecetaInput[]
): Promise<DetalleRecetaItem[]> => {
  const res = await api.put<DetalleRecetaItem[]>(`/ingredientes/productos/${productoId}/receta`, lineas)
  return res.data
}

export const getCostoUtilidadProductoApi = async (productoId: number): Promise<AnalisisCostoItem> => {
  const res = await api.get<AnalisisCostoItem>(`/ingredientes/productos/${productoId}/costo-utilidad`)
  return res.data
}

export const getPreparadosApi = async (estado = 'DISPONIBLE'): Promise<PreparadoAdminItem[]> => {
  const res = await api.get<PreparadoAdminItem[]>('/preparados', { params: { estado } })
  return res.data
}

export const descartarPreparadoApi = async (id: number, motivo: string): Promise<void> => {
  await api.post(`/preparados/${id}/descartar`, { motivo })
}

let _configCache: Record<string, string> | null = null
let _configTimestamp = 0

export const getConfiguracionApi = async (): Promise<
  { clave: string; valor: string; descripcion?: string }[]
> => {
  const res = await api.get('/admin/configuracion')
  return res.data
}

export const getParametrosConfiguracion = async (forceRefresh = false): Promise<Record<string, string>> => {
  const now = Date.now()
  if (!forceRefresh && _configCache && (now - _configTimestamp < 30000)) {
    return _configCache
  }
  try {
    const data = await getConfiguracionApi()
    const mapa: Record<string, string> = {}
    for (const item of data) {
      mapa[item.clave] = item.valor
    }
    _configCache = mapa
    _configTimestamp = now
    return mapa
  } catch {
    return _configCache || {}
  }
}

export const setConfiguracionApi = async (
  clave: string,
  valor: string
): Promise<any> => {
  _configCache = null
  const res = await api.put(`/admin/configuracion/${clave}`, { valor })
  return res.data
}

export const getUsuariosApi = async (): Promise<UsuarioAdminItem[]> => {
  const res = await api.get<UsuarioAdminItem[]>('/admin/usuarios')
  return res.data
}

export const crearUsuarioApi = async (data: UsuarioCreateInput): Promise<UsuarioAdminItem> => {
  const res = await api.post<UsuarioAdminItem>('/admin/usuarios', data)
  return res.data
}

export const resetPasswordUsuarioApi = async (
  usuarioId: number,
  nuevaPassword: string
): Promise<{ status: string; mensaje: string }> => {
  const res = await api.put(`/admin/usuarios/${usuarioId}/password`, {
    nueva_password: nuevaPassword,
  })
  return res.data
}

export const cambiarEstadoUsuarioApi = async (
  usuarioId: number,
  activo: boolean
): Promise<UsuarioAdminItem> => {
  const res = await api.put<UsuarioAdminItem>(`/admin/usuarios/${usuarioId}/estado`, { activo })
  return res.data
}

export const crearProductoApi = async (data: {
  categoria_id: number
  nombre: string
  descripcion?: string
  precio: number
  iva_incluido?: boolean
  empaque_llevar_id?: number | null
  permite_adiciones?: boolean
}): Promise<Producto> => {
  const res = await api.post<Producto>('/productos', data)
  return res.data
}

export const actualizarProductoApi = async (
  id: number,
  data: Partial<{
    categoria_id: number
    nombre: string
    descripcion: string
    precio: number
    iva_incluido: boolean
    manual_disponible: boolean | null
    empaque_llevar_id: number | null
    permite_adiciones: boolean
  }>
): Promise<Producto> => {
  const res = await api.put<Producto>(`/productos/${id}`, data)
  return res.data
}

export const eliminarProductoApi = async (id: number): Promise<void> => {
  await api.delete(`/productos/${id}`)
}

export const getComponentesComboApi = async (
  productoId: number
): Promise<Array<{
  id: number
  producto_hijo_id: number
  producto_hijo_nombre: string
  cantidad: number
  precio_unitario: number
}>> => {
  const res = await api.get(`/ingredientes/combos/${productoId}/componentes`)
  return res.data
}

export const guardarComponentesComboApi = async (
  productoId: number,
  componentes: Array<{ producto_hijo_id: number; cantidad: number }>
): Promise<any> => {
  const res = await api.put(`/ingredientes/combos/${productoId}/componentes`, componentes)
  return res.data
}

export const getAdicionesConfigApi = async (): Promise<AdicionExtra[]> => {
  const res = await api.get<AdicionExtra[]>('/productos/adiciones/configuracion')
  return res.data
}

export const guardarAdicionesConfigApi = async (adiciones: AdicionExtra[]): Promise<AdicionExtra[]> => {
  const res = await api.put<AdicionExtra[]>('/productos/adiciones/configuracion', adiciones)
  return res.data
}

export const cambiarMarcasUsuarioApi = async (
  usuarioId: number,
  data: { fijado?: boolean; es_demo?: boolean }
): Promise<UsuarioAdminItem> => {
  const res = await api.put<UsuarioAdminItem>(`/admin/usuarios/${usuarioId}/marcas`, data)
  return res.data
}

export const getResetResumenApi = async (): Promise<ResetResumenOut> => {
  const res = await api.get<ResetResumenOut>('/admin/sistema/reset/resumen')
  return res.data
}

export const resetSistemaApi = async (
  data: ResetSistemaInput
): Promise<{ status: string; mensaje: string; detalle: Record<string, any> }> => {
  const res = await api.post<{ status: string; mensaje: string; detalle: Record<string, any> }>(
    '/admin/sistema/reset',
    data
  )
  return res.data
}


