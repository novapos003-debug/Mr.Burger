import api from './client'
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
  unidad_base: string
  costo_unitario?: number
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

export const getConfiguracionApi = async (): Promise<
  { clave: string; valor: string; descripcion?: string }[]
> => {
  const res = await api.get('/admin/configuracion')
  return res.data
}

export const setConfiguracionApi = async (
  clave: string,
  valor: string
): Promise<any> => {
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

