import React, { useState, useEffect, useMemo } from 'react'
import {
  Boxes,
  Plus,
  Search,
  AlertTriangle,
  RefreshCw,
  History,
  Scale,
  X,
  Layers,
  DollarSign,
  TrendingDown,
  ShieldAlert,
  Pencil,
} from 'lucide-react'
import {
  getIngredientesApi,
  getCategoriasInsumoApi,
  crearIngredienteApi,
  actualizarIngredienteApi,
  getMovimientosIngredienteApi,
  crearCategoriaInsumoApi,
  getConfiguracionApi,
  setConfiguracionApi,
} from '../../api/admin'
import type {
  IngredienteItem,
  CategoriaInsumoItem,
  MovimientoInventarioItem,
} from '../../types/admin'

export const InventarioTab: React.FC = () => {
  const [ingredientes, setIngredientes] = useState<IngredienteItem[]>([])
  const [categorias, setCategorias] = useState<CategoriaInsumoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busqueda, setBusqueda] = useState('')
  const [categoriaFiltro, setCategoriaFiltro] = useState<number | null>(null)
  const [politicaStock, setPoliticaStock] = useState<string>('ADVERTIR_Y_PERMITIR')

  // Feedback
  const [mensajeExito, setMensajeExito] = useState<string | null>(null)

  // Modal Nuevo Insumo
  const [isNuevoInsumoOpen, setIsNuevoInsumoOpen] = useState(false)
  const [nombreInsumo, setNombreInsumo] = useState('')
  const [categoriaInsumoId, setCategoriaInsumoId] = useState<number | ''>('')
  const [tipoArticulo, setTipoArticulo] = useState<string>('INSUMO_RECETA')
  const [unidadBase, setUnidadBase] = useState('GRAMO')
  const [costoUnitario, setCostoUnitario] = useState<number>(0)
  const [precioVenta, setPrecioVenta] = useState<number>(0)
  const [stockActual, setStockActual] = useState<number>(0)
  const [stockMinimo, setStockMinimo] = useState<number>(100)
  const [guardandoInsumo, setGuardandoInsumo] = useState(false)

  // Filtro de tipo de artículo
  const [tipoArticuloFiltro, setTipoArticuloFiltro] = useState<string>('TODOS')

  // Modal Nueva Categoría
  const [isNuevaCatOpen, setIsNuevaCatOpen] = useState(false)
  const [nombreCat, setNombreCat] = useState('')
  const [descCat, setDescCat] = useState('')
  const [guardandoCat, setGuardandoCat] = useState(false)

  // Modal Ajuste Manual
  const [insumoAjustando, setInsumoAjustando] = useState<IngredienteItem | null>(null)
  const [nuevoStock, setNuevoStock] = useState<number>(0)
  const [motivoAjuste, setMotivoAjuste] = useState('')
  const [guardandoAjuste, setGuardandoAjuste] = useState(false)

  // Modal Editar Insumo
  const [insumoEditando, setInsumoEditando] = useState<IngredienteItem | null>(null)
  const [editNombre, setEditNombre] = useState('')
  const [editCategoriaId, setEditCategoriaId] = useState<number | ''>('')
  const [editTipoArticulo, setEditTipoArticulo] = useState<string>('INSUMO_RECETA')
  const [editCostoUnitario, setEditCostoUnitario] = useState<number>(0)
  const [editPrecioVenta, setEditPrecioVenta] = useState<number>(0)
  const [editStockMinimo, setEditStockMinimo] = useState<number>(0)
  const [guardandoEdicion, setGuardandoEdicion] = useState(false)

  // Modal Kardex / Movimientos
  const [insumoKardex, setInsumoKardex] = useState<IngredienteItem | null>(null)
  const [movimientos, setMovimientos] = useState<MovimientoInventarioItem[]>([])
  const [kardexLoading, setKardexLoading] = useState(false)

  const cargarDatos = async () => {
    setLoading(true)
    setError(null)
    try {
      const [ings, cats, cfgs] = await Promise.all([
        getIngredientesApi(),
        getCategoriasInsumoApi(),
        getConfiguracionApi(),
      ])
      setIngredientes(ings)
      setCategorias(cats)
      const pol = cfgs.find((c) => c.clave === 'politica_stock_insuficiente')
      if (pol) setPoliticaStock(pol.valor.trim().toUpperCase())
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar inventario')
    } finally {
      setLoading(false)
    }
  }

  const handleCambiarPolitica = async (nueva: string) => {
    try {
      await setConfiguracionApi('politica_stock_insuficiente', nueva)
      setPoliticaStock(nueva)
      setMensajeExito(
        `Política de stock actualizada: ${
          nueva === 'BLOQUEAR'
            ? 'BLOQUEAR VENTAS (Estricto)'
            : 'ADVERTIR Y PERMITIR (Flexible)'
        }`
      )
    } catch {
      setError('Error al actualizar la política de stock')
    }
  }

  useEffect(() => {
    cargarDatos()
  }, [])

  // Estadísticas Rápidas
  const stats = useMemo(() => {
    const totalInsumos = ingredientes.length
    const agotados = ingredientes.filter((i) => i.stock_actual <= 0).length
    const stockBajo = ingredientes.filter((i) => i.stock_actual > 0 && i.stock_actual <= i.stock_minimo).length
    const valorInventario = ingredientes.reduce(
      (acc, i) => acc + Number(i.stock_actual || 0) * Number(i.costo_unitario || 0),
      0
    )
    return { totalInsumos, agotados, stockBajo, valorInventario }
  }, [ingredientes])

  // Filtrado
  const ingredientesFiltrados = useMemo(() => {
    return ingredientes.filter((i) => {
      const matchCat = categoriaFiltro === null || i.categoria_insumo_id === categoriaFiltro
      const matchTipo =
        tipoArticuloFiltro === 'TODOS' ||
        (tipoArticuloFiltro === 'DESECHABLE_SERVICIO' && i.tipo_articulo === 'DESECHABLE_SERVICIO') ||
        (tipoArticuloFiltro === 'GASTO_OPERATIVO' && i.tipo_articulo === 'GASTO_OPERATIVO') ||
        (tipoArticuloFiltro === 'INSUMO_RECETA' && (i.tipo_articulo === 'INSUMO_RECETA' || !i.tipo_articulo))
      const matchText =
        i.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
        (i.categoria_insumo_nombre && i.categoria_insumo_nombre.toLowerCase().includes(busqueda.toLowerCase()))
      return matchCat && matchTipo && matchText
    })
  }, [ingredientes, categoriaFiltro, tipoArticuloFiltro, busqueda])

  // Guardar Nuevo Insumo
  const handleCrearInsumo = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!nombreInsumo.trim()) return
    const esEmpaque = tipoArticulo === 'DESECHABLE_SERVICIO' || Number(categoriaInsumoId) === 8
    setGuardandoInsumo(true)
    try {
      await crearIngredienteApi({
        nombre: nombreInsumo.trim(),
        categoria_insumo_id: categoriaInsumoId === '' ? null : Number(categoriaInsumoId),
        tipo_articulo: esEmpaque ? 'DESECHABLE_SERVICIO' : tipoArticulo,
        unidad_base: unidadBase,
        costo_unitario: Number(costoUnitario),
        precio_venta: esEmpaque ? Number(precioVenta) : 0,
        stock_actual: Number(stockActual),
        stock_minimo: Number(stockMinimo),
      })
      setMensajeExito(`✓ Insumo "${nombreInsumo}" creado exitosamente.`)
      setIsNuevoInsumoOpen(false)
      setNombreInsumo('')
      setCostoUnitario(0)
      setPrecioVenta(0)
      setStockActual(0)
      cargarDatos()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al crear insumo')
    } finally {
      setGuardandoInsumo(false)
    }
  }

  // Guardar Nueva Categoría
  const handleCrearCategoria = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!nombreCat.trim()) return
    setGuardandoCat(true)
    try {
      await crearCategoriaInsumoApi({
        nombre: nombreCat.trim(),
        descripcion: descCat.trim() || undefined,
      })
      setMensajeExito(`✓ Categoría "${nombreCat}" creada.`)
      setIsNuevaCatOpen(false)
      setNombreCat('')
      setDescCat('')
      const cats = await getCategoriasInsumoApi()
      setCategorias(cats)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al crear categoría')
    } finally {
      setGuardandoCat(false)
    }
  }

  // Guardar Ajuste Manual de Stock
  const handleGuardarAjuste = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!insumoAjustando) return
    setGuardandoAjuste(true)
    try {
      await actualizarIngredienteApi(insumoAjustando.id, {
        stock_actual: Number(nuevoStock),
      })
      setMensajeExito(`✓ Stock de ${insumoAjustando.nombre} ajustado a ${nuevoStock} ${insumoAjustando.unidad_base}.`)
      setInsumoAjustando(null)
      cargarDatos()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al ajustar stock')
    } finally {
      setGuardandoAjuste(false)
    }
  }

  // Abrir Modal Editar Insumo
  const handleAbrirEditar = (ing: IngredienteItem) => {
    setInsumoEditando(ing)
    setEditNombre(ing.nombre)
    setEditCategoriaId(ing.categoria_insumo_id ?? '')
    setEditTipoArticulo(ing.tipo_articulo || 'INSUMO_RECETA')
    setEditCostoUnitario(Number(ing.costo_unitario) || 0)
    setEditPrecioVenta(Number(ing.precio_venta) || 0)
    setEditStockMinimo(Number(ing.stock_minimo) || 0)
  }

  // Guardar Edición de Insumo
  const handleGuardarEdicion = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!insumoEditando) return
    setGuardandoEdicion(true)
    const esEmpaque = editTipoArticulo === 'DESECHABLE_SERVICIO' || editCategoriaId === 8
    try {
      await actualizarIngredienteApi(insumoEditando.id, {
        nombre: editNombre.trim(),
        categoria_insumo_id: editCategoriaId === '' ? null : Number(editCategoriaId),
        tipo_articulo: esEmpaque ? 'DESECHABLE_SERVICIO' : editTipoArticulo,
        costo_unitario: Number(editCostoUnitario),
        precio_venta: esEmpaque ? Number(editPrecioVenta) : 0,
        stock_minimo: Number(editStockMinimo),
      })
      setMensajeExito(`✓ Insumo "${editNombre.trim()}" actualizado correctamente.`)
      setInsumoEditando(null)
      cargarDatos()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al actualizar insumo')
    } finally {
      setGuardandoEdicion(false)
    }
  }

  // Abrir Kardex
  const handleAbrirKardex = async (insumo: IngredienteItem) => {
    setInsumoKardex(insumo)
    setKardexLoading(true)
    try {
      const movs = await getMovimientosIngredienteApi(insumo.id)
      setMovimientos(movs)
    } catch (err: any) {
      alert('Error al consultar movimientos')
    } finally {
      setKardexLoading(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Banner de Éxito */}
      {mensajeExito && (
        <div className="p-3 bg-emerald-950/80 border border-emerald-800 text-emerald-300 rounded-xl text-xs flex items-center justify-between">
          <span>{mensajeExito}</span>
          <button onClick={() => setMensajeExito(null)} className="text-emerald-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-950/70 border border-red-800 rounded-xl text-red-200 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Cards de Inventario */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-3 sm:p-4 shadow-lg min-w-0 overflow-hidden flex flex-col justify-between">
          <span className="text-slate-400 text-xs font-semibold flex items-center gap-1.5 mb-1 truncate">
            <Boxes className="w-3.5 h-3.5 text-purple-400 shrink-0" />
            <span className="truncate">Total Insumos</span>
          </span>
          <p className="text-lg sm:text-2xl font-black text-white truncate">{stats.totalInsumos}</p>
          <span className="text-[10px] text-slate-500 truncate">Materias primas</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-3 sm:p-4 shadow-lg min-w-0 overflow-hidden flex flex-col justify-between">
          <span className="text-slate-400 text-xs font-semibold flex items-center gap-1.5 mb-1 truncate">
            <TrendingDown className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="truncate">Stock Bajo</span>
          </span>
          <p className={`text-lg sm:text-2xl font-black truncate ${stats.stockBajo > 0 ? 'text-amber-400' : 'text-slate-200'}`}>
            {stats.stockBajo}
          </p>
          <span className="text-[10px] text-slate-500 truncate">Bajo el mínimo</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-3 sm:p-4 shadow-lg min-w-0 overflow-hidden flex flex-col justify-between">
          <span className="text-slate-400 text-xs font-semibold flex items-center gap-1.5 mb-1 truncate">
            <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0" />
            <span className="truncate">Agotados (0)</span>
          </span>
          <p className={`text-lg sm:text-2xl font-black truncate ${stats.agotados > 0 ? 'text-red-400' : 'text-slate-200'}`}>
            {stats.agotados}
          </p>
          <span className="text-[10px] text-slate-500 truncate">Impiden preparar</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-3 sm:p-4 shadow-lg min-w-0 overflow-hidden flex flex-col justify-between">
          <span className="text-slate-400 text-xs font-semibold flex items-center gap-1.5 mb-1 truncate">
            <DollarSign className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span className="truncate">Valor Valorizado</span>
          </span>
          <p className="text-sm sm:text-lg lg:text-xl font-black text-emerald-400 font-mono truncate" title={`$${stats.valorInventario.toLocaleString('es-CO')}`}>
            ${stats.valorInventario.toLocaleString('es-CO')}
          </p>
          <span className="text-[10px] text-slate-500 truncate">Capital en stock</span>
        </div>
      </div>

      {/* Selector de Política de Control de Stock */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-orange-600/20 text-orange-400 flex items-center justify-center shrink-0">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white">Política ante Faltante de Stock:</span>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  politicaStock === 'BLOQUEAR'
                    ? 'bg-orange-950 text-orange-400 border border-orange-800'
                    : 'bg-amber-950 text-amber-400 border border-amber-800'
                }`}
              >
                {politicaStock === 'BLOQUEAR' ? 'ESTRICTA (BLOQUEO)' : 'FLEXIBLE (PERMISIVA)'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {politicaStock === 'BLOQUEAR'
                ? 'Impide enviar pedidos a cocina si falta materia prima para la receta.'
                : 'Permite tomar pedidos y vender en horas pico llevando el inventario a negativo temporal.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
          <button
            type="button"
            onClick={() => handleCambiarPolitica('BLOQUEAR')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition cursor-pointer ${
              politicaStock === 'BLOQUEAR'
                ? 'bg-orange-600 text-white shadow-lg shadow-orange-600/30'
                : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Bloquear Ventas
          </button>
          <button
            type="button"
            onClick={() => handleCambiarPolitica('ADVERTIR_Y_PERMITIR')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition cursor-pointer ${
              politicaStock === 'ADVERTIR_Y_PERMITIR'
                ? 'bg-amber-600 text-white shadow-lg shadow-amber-600/30'
                : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Permitir (Flexible)
          </button>
        </div>
      </div>

      {/* Barra de Acciones y Filtros */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-lg space-y-3">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar materia prima (papa, carne, pan, queso...)"
              className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsNuevaCatOpen(true)}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition flex items-center gap-1.5 cursor-pointer"
            >
              <Layers className="w-3.5 h-3.5 text-purple-400" />
              <span>+ Categoría</span>
            </button>

            <button
              onClick={() => setIsNuevoInsumoOpen(true)}
              className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold transition shadow-lg shadow-purple-950/40 flex items-center gap-1.5 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>+ Nuevo Insumo</span>
            </button>
          </div>
        </div>

        {/* Filtro por Categoría */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
          <button
            onClick={() => setCategoriaFiltro(null)}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer ${
              categoriaFiltro === null
                ? 'bg-purple-600 text-white shadow-md'
                : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            Todos ({ingredientes.length})
          </button>
          {categorias.map((cat) => {
            const count = ingredientes.filter((i) => i.categoria_insumo_id === cat.id).length
            return (
              <button
                key={cat.id}
                onClick={() => setCategoriaFiltro(cat.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer flex items-center gap-1.5 ${
                  categoriaFiltro === cat.id
                    ? 'bg-purple-600 text-white shadow-md'
                    : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                <span>{cat.nombre}</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-300">
                  {count}
                </span>
              </button>
            )
          })}
        </div>

        {/* Filtro por Tipo de Artículo (Insumos vs Empaques vs Gastos) */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none pt-2 border-t border-slate-800/80">
          {[
            { id: 'TODOS', label: 'Todos los Artículos' },
            { id: 'INSUMO_RECETA', label: '🥩 Insumos de Cocina' },
            { id: 'DESECHABLE_SERVICIO', label: '🥡 Empaques y Desechables (C1, P1, Bolsas...)' },
            { id: 'GASTO_OPERATIVO', label: '🧼 Gastos Operativos (Aseo, Papel...)' },
          ].map((f) => {
            const count =
              f.id === 'TODOS'
                ? ingredientes.length
                : f.id === 'INSUMO_RECETA'
                ? ingredientes.filter((i) => i.tipo_articulo === 'INSUMO_RECETA' || !i.tipo_articulo).length
                : ingredientes.filter((i) => i.tipo_articulo === f.id).length
            const isSelected = tipoArticuloFiltro === f.id
            return (
              <button
                key={f.id}
                onClick={() => setTipoArticuloFiltro(f.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition cursor-pointer flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-gradient-to-r from-orange-600 to-amber-600 text-white shadow-md'
                    : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                <span>{f.label}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold ${
                    isSelected ? 'bg-orange-900 text-white' : 'bg-slate-800 text-slate-300'
                  }`}
                >
                  {count}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Tabla de Insumos */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 font-bold uppercase tracking-wider">
              <tr>
                <th className="p-3.5">Materia Prima / Insumo</th>
                <th className="p-3.5">Categoría</th>
                <th className="p-3.5 text-right">Stock Actual</th>
                <th className="p-3.5 text-right">Stock Mínimo</th>
                <th className="p-3.5 text-right">Costo Unitario</th>
                <th className="p-3.5 text-right">Valor Total</th>
                <th className="p-3.5 text-center">Estado</th>
                <th className="p-3.5 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-slate-500">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-purple-500 mb-2" />
                    Cargando inventario...
                  </td>
                </tr>
              ) : ingredientesFiltrados.length > 0 ? (
                ingredientesFiltrados.map((ing) => {
                  const stock = Number(ing.stock_actual || 0)
                  const min = Number(ing.stock_minimo || 0)
                  const costo = Number(ing.costo_unitario || 0)
                  const total = stock * costo

                  let estadoBadge = (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">
                      Óptimo
                    </span>
                  )
                  if (stock < 0) {
                    estadoBadge = (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-950/80 text-purple-300 border border-purple-700/80 flex items-center justify-center gap-1" title="Ventas permitidas en negativo. Reconciliar al cargar inventario diario.">
                        Negativo ({stock.toLocaleString('es-CO')})
                      </span>
                    )
                  } else if (stock === 0) {
                    estadoBadge = (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-950/80 text-red-400 border border-red-800/80 animate-pulse">
                        Agotado (0)
                      </span>
                    )
                  } else if (stock <= min) {
                    estadoBadge = (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-950/80 text-amber-400 border border-amber-800/80">
                        Bajo
                      </span>
                    )
                  }

                  return (
                    <tr key={ing.id} className="hover:bg-slate-800/40 transition">
                      <td className="p-3.5 font-bold text-white">
                        <div className="flex items-center gap-2">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              ing.tipo_articulo === 'DESECHABLE_SERVICIO'
                                ? 'bg-orange-500'
                                : ing.tipo_articulo === 'GASTO_OPERATIVO'
                                ? 'bg-rose-500'
                                : 'bg-purple-500'
                            }`}
                          />
                          <span>{ing.nombre}</span>
                        </div>
                        <div className="flex flex-wrap gap-1 mt-1 pl-4">
                          {ing.tipo_articulo === 'DESECHABLE_SERVICIO' && (
                            <span className="text-[9px] bg-orange-950/80 text-orange-300 border border-orange-800/80 px-1.5 py-0.2 rounded font-semibold">
                              🥡 Empaque / Para Llevar
                            </span>
                          )}
                          {ing.tipo_articulo === 'GASTO_OPERATIVO' && (
                            <span className="text-[9px] bg-rose-950/80 text-rose-300 border border-rose-800/80 px-1.5 py-0.2 rounded font-semibold">
                              🧼 Gasto Operativo
                            </span>
                          )}
                          {Number(ing.precio_venta || 0) > 0 && (
                            <span className="text-[9px] bg-emerald-950/80 text-emerald-300 border border-emerald-800/80 px-1.5 py-0.2 rounded font-mono font-bold">
                              Llevar: ${Number(ing.precio_venta).toLocaleString('es-CO')}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-3.5 text-slate-400">
                        <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-[10px] font-semibold">
                          {ing.categoria_insumo_nombre || 'Sin categoría'}
                        </span>
                      </td>
                      <td className={`p-3.5 text-right font-mono font-bold ${stock < 0 ? 'text-purple-400' : stock === 0 ? 'text-red-400' : 'text-white'}`}>
                        {stock.toLocaleString('es-CO')} <span className="text-slate-400 font-normal">{ing.unidad_base}</span>
                      </td>
                      <td className="p-3.5 text-right font-mono text-slate-400">
                        {min.toLocaleString('es-CO')} {ing.unidad_base}
                      </td>
                      <td className="p-3.5 text-right font-mono text-emerald-400">
                        ${costo.toLocaleString('es-CO')}
                      </td>
                      <td className="p-3.5 text-right font-mono font-bold text-emerald-400">
                        ${total.toLocaleString('es-CO')}
                      </td>
                      <td className="p-3.5 text-center">{estadoBadge}</td>
                      <td className="p-3.5 text-center">
                        <div className="flex items-center justify-center gap-1.5">
                          <button
                            onClick={() => handleAbrirEditar(ing)}
                            className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-[11px] font-bold transition flex items-center gap-1 cursor-pointer"
                            title="Editar Insumo (Precio, nombre, categoría, stock mínimo)"
                          >
                            <Pencil className="w-3 h-3 text-amber-400" />
                            <span>Editar</span>
                          </button>

                          <button
                            onClick={() => {
                              setInsumoAjustando(ing)
                              setNuevoStock(Number(ing.stock_actual))
                              setMotivoAjuste('Ajuste de inventario físico')
                            }}
                            className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-[11px] font-bold transition flex items-center gap-1 cursor-pointer"
                            title="Ajustar Stock Manualmente"
                          >
                            <Scale className="w-3 h-3 text-purple-400" />
                            <span>Ajustar</span>
                          </button>

                          <button
                            onClick={() => handleAbrirKardex(ing)}
                            className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-[11px] font-bold transition flex items-center gap-1 cursor-pointer"
                            title="Ver Kardex / Historial de Movimientos"
                          >
                            <History className="w-3 h-3 text-sky-400" />
                            <span>Kardex</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan={8} className="text-center py-10 text-slate-500">
                    No se encontraron insumos con los filtros actuales.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ======================================================== */}
      {/* MODAL 1: NUEVO INSUMO */}
      {/* ======================================================== */}
      {isNuevoInsumoOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-5 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <h3 className="text-sm font-black text-white flex items-center gap-2">
                <Plus className="w-4 h-4 text-purple-400" />
                Registrar Nueva Materia Prima / Insumo
              </h3>
              <button onClick={() => setIsNuevoInsumoOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCrearInsumo} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-bold mb-1">Nombre del Insumo / Artículo</label>
                <input
                  type="text"
                  required
                  value={nombreInsumo}
                  onChange={(e) => setNombreInsumo(e.target.value)}
                  placeholder="Ej: Papa criolla, Caja C1, Bolsa T25, Jabón Axion..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-bold mb-1">Tipo de Artículo / Destino</label>
                <select
                  value={tipoArticulo}
                  onChange={(e) => setTipoArticulo(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white font-bold focus:outline-none focus:border-purple-500"
                >
                  <option value="INSUMO_RECETA">🥩 INSUMO DE COCINA (Carne, pan, vegetales, salsas...)</option>
                  <option value="DESECHABLE_SERVICIO">🥡 EMPAQUE / DESECHABLE (Cajas C1, P1, Bolsas T20-T40, vasos...)</option>
                  <option value="GASTO_OPERATIVO">🧼 GASTO OPERATIVO (Jabón Axion, esponjas, papel higiénico, cocina...)</option>
                </select>
              </div>

              {(tipoArticulo === 'DESECHABLE_SERVICIO' || Number(categoriaInsumoId) === 8) && (
                <div className="p-3 bg-orange-950/40 border border-orange-800/60 rounded-xl space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="block text-orange-300 font-bold text-xs">
                      Precio de Venta al Cliente para Llevar ($ COP)
                    </label>
                    <span className="text-[10px] text-orange-400 font-mono font-bold">Cargo por empaque</span>
                  </div>
                  <input
                    type="number"
                    min="0"
                    step="100"
                    value={precioVenta}
                    onChange={(e) => setPrecioVenta(parseFloat(e.target.value) || 0)}
                    placeholder="Ej: 1500 (para C1) o 500 (para P1) o 0"
                    className="w-full bg-slate-900 border border-orange-700/80 rounded-lg p-2 text-emerald-400 font-mono font-bold text-sm focus:outline-none"
                  />
                  <p className="text-[10px] text-orange-300/80 leading-tight">
                    💡 Si se incluye en la receta marcado como <strong>"Solo Llevar"</strong>, este precio se sumará automáticamente a la cuenta final cuando el pedido sea para llevar.
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-bold mb-1">Categoría</label>
                  <select
                    value={categoriaInsumoId}
                    onChange={(e) => setCategoriaInsumoId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="">(Sin categoría)</option>
                    {categorias.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.nombre}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 font-bold mb-1">Unidad Base</label>
                  <select
                    value={unidadBase}
                    onChange={(e) => setUnidadBase(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-purple-500 font-bold"
                  >
                    <option value="GRAMO">GRAMO (Masa: carne, verduras)</option>
                    <option value="MILILITRO">MILILITRO (Volumen: aceites, salsas)</option>
                    <option value="UNIDAD">UNIDAD (Pan, salchicha, huevos)</option>
                    <option value="LONJA">LONJA (Queso, tocineta)</option>
                    <option value="PORCION">PORCION</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-slate-400 font-bold mb-1">Costo Unit ($)</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={costoUnitario}
                    onChange={(e) => setCostoUnitario(parseFloat(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2 text-white font-mono text-center font-bold"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 font-bold mb-1">Stock Inicial</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={stockActual}
                    onChange={(e) => setStockActual(parseFloat(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2 text-white font-mono text-center font-bold"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 font-bold mb-1">Stock Mínimo</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={stockMinimo}
                    onChange={(e) => setStockMinimo(parseFloat(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2 text-white font-mono text-center font-bold"
                  />
                </div>
              </div>

              <div className="pt-3 flex justify-end gap-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsNuevoInsumoOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-white"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={guardandoInsumo}
                  className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 font-bold text-white shadow-lg"
                >
                  {guardandoInsumo ? 'Guardando...' : 'Crear Insumo'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL 2: NUEVA CATEGORÍA */}
      {/* ======================================================== */}
      {isNuevaCatOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-sm p-5 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <h3 className="text-sm font-black text-white flex items-center gap-2">
                <Layers className="w-4 h-4 text-purple-400" />
                Nueva Categoría de Insumos
              </h3>
              <button onClick={() => setIsNuevaCatOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCrearCategoria} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-bold mb-1">Nombre de la Categoría</label>
                <input
                  type="text"
                  required
                  value={nombreCat}
                  onChange={(e) => setNombreCat(e.target.value)}
                  placeholder="Ej: SALSAS, CONGELADOS, DESECHABLES..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white uppercase focus:outline-none focus:border-purple-500 font-bold"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-bold mb-1">Descripción (Opcional)</label>
                <input
                  type="text"
                  value={descCat}
                  onChange={(e) => setDescCat(e.target.value)}
                  placeholder="Detalle o uso principal..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="pt-3 flex justify-end gap-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsNuevaCatOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-white"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={guardandoCat}
                  className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 font-bold text-white shadow-lg"
                >
                  {guardandoCat ? 'Guardando...' : 'Crear Categoría'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL 3: AJUSTE MANUAL DE INVENTARIO */}
      {/* ======================================================== */}
      {insumoAjustando && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-5 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <h3 className="text-sm font-black text-white flex items-center gap-2">
                <Scale className="w-4 h-4 text-purple-400" />
                Ajustar Stock Físico: {insumoAjustando.nombre}
              </h3>
              <button onClick={() => setInsumoAjustando(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleGuardarAjuste} className="space-y-3 text-xs">
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex justify-between items-center">
                <span className="text-slate-400 font-bold">Stock Actual en Sistema:</span>
                <span className="font-mono text-white font-bold text-sm">
                  {insumoAjustando.stock_actual} {insumoAjustando.unidad_base}
                </span>
              </div>

              <div>
                <label className="block text-slate-400 font-bold mb-1">
                  Nuevo Conteo Físico Real ({insumoAjustando.unidad_base})
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={nuevoStock}
                  onChange={(e) => setNuevoStock(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white font-mono text-center font-bold text-lg focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-bold mb-1">
                  Motivo del Ajuste (Auditoría obligatoria)
                </label>
                <input
                  type="text"
                  required
                  value={motivoAjuste}
                  onChange={(e) => setMotivoAjuste(e.target.value)}
                  placeholder="Ej: Cuadre semanal, merma por descomposición, etc."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="pt-3 flex justify-end gap-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setInsumoAjustando(null)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-white"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={guardandoAjuste}
                  className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 font-bold text-white shadow-lg"
                >
                  {guardandoAjuste ? 'Guardando...' : 'Confirmar Ajuste y Auditar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL 4: KARDEX / HISTORIAL DE MOVIMIENTOS */}
      {/* ======================================================== */}
      {insumoKardex && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl">
            <div className="p-4 border-b border-slate-800 flex justify-between items-center shrink-0">
              <div>
                <h3 className="text-base font-black text-white flex items-center gap-2">
                  <History className="w-5 h-5 text-sky-400" />
                  Kardex / Historial de Insumo: {insumoKardex.nombre}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Trazabilidad inmutable de entradas, salidas y consumos por venta en cocina.
                </p>
              </div>
              <button onClick={() => setInsumoKardex(null)} className="text-slate-400 hover:text-white p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {kardexLoading ? (
                <div className="py-16 text-center text-slate-500 text-xs">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto text-sky-400 mb-2" />
                  Consultando extracto de movimientos...
                </div>
              ) : movimientos.length > 0 ? (
                <div className="border border-slate-800 rounded-xl overflow-hidden shadow-inner">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 font-bold uppercase">
                      <tr>
                        <th className="p-2.5">Fecha</th>
                        <th className="p-2.5">Tipo</th>
                        <th className="p-2.5 text-right">Cantidad</th>
                        <th className="p-2.5 text-right">Saldo Ant.</th>
                        <th className="p-2.5 text-right">Saldo Nuevo</th>
                        <th className="p-2.5">Referencia</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 font-mono">
                      {movimientos.map((m) => {
                        const isSalida = Number(m.cantidad) < 0
                        return (
                          <tr key={m.id} className="hover:bg-slate-800/40 transition">
                            <td className="p-2.5 text-slate-400">
                              {new Date(m.creado_en).toLocaleString('es-CO')}
                            </td>
                            <td className="p-2.5">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  m.tipo === 'VENTA'
                                    ? 'bg-orange-950/60 text-orange-400 border border-orange-800/60'
                                    : m.tipo === 'COMPRA'
                                    ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/60'
                                    : 'bg-purple-950/60 text-purple-400 border border-purple-800/60'
                                }`}
                              >
                                {m.tipo}
                              </span>
                            </td>
                            <td
                              className={`p-2.5 text-right font-bold ${
                                isSalida ? 'text-rose-400' : 'text-emerald-400'
                              }`}
                            >
                              {Number(m.cantidad).toLocaleString('es-CO')} {m.unidad}
                            </td>
                            <td className="p-2.5 text-right text-slate-400">
                              {m.saldo_anterior !== null && m.saldo_anterior !== undefined
                                ? Number(m.saldo_anterior).toLocaleString('es-CO')
                                : '-'}
                            </td>
                            <td className="p-2.5 text-right font-bold text-white">
                              {m.saldo_nuevo !== null && m.saldo_nuevo !== undefined
                                ? Number(m.saldo_nuevo).toLocaleString('es-CO')
                                : '-'}
                            </td>
                            <td className="p-2.5 text-slate-300 font-sans">{m.referencia || '-'}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-12 text-center text-slate-500 text-xs">
                  No hay movimientos registrados para este insumo.
                </div>
              )}
            </div>

            <div className="p-3 border-t border-slate-800 bg-slate-950 flex justify-end shrink-0">
              <button
                onClick={() => setInsumoKardex(null)}
                className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-bold"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL 5: EDITAR INSUMO (PRECIO / COSTO, NOMBRE, ETC.) */}
      {/* ======================================================== */}
      {insumoEditando && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-5 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <h3 className="text-sm font-black text-white flex items-center gap-2">
                <Pencil className="w-4 h-4 text-amber-400" />
                Editar Insumo: {insumoEditando.nombre}
              </h3>
              <button onClick={() => setInsumoEditando(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleGuardarEdicion} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-bold mb-1">Nombre del Insumo / Artículo</label>
                <input
                  type="text"
                  required
                  value={editNombre}
                  onChange={(e) => setEditNombre(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-purple-500 font-bold"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-bold mb-1">Tipo de Artículo / Destino</label>
                <select
                  value={editTipoArticulo}
                  onChange={(e) => setEditTipoArticulo(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white font-bold focus:outline-none focus:border-purple-500"
                >
                  <option value="INSUMO_RECETA">🥩 INSUMO DE COCINA (Carne, pan, vegetales, salsas...)</option>
                  <option value="DESECHABLE_SERVICIO">🥡 EMPAQUE / DESECHABLE (Cajas C1, P1, Bolsas T20-T40, vasos...)</option>
                  <option value="GASTO_OPERATIVO">🧼 GASTO OPERATIVO (Jabón Axion, esponjas, papel higiénico, cocina...)</option>
                </select>
              </div>

              {(editTipoArticulo === 'DESECHABLE_SERVICIO' || Number(editCategoriaId) === 8) && (
                <div className="p-3 bg-orange-950/40 border border-orange-800/60 rounded-xl space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="block text-orange-300 font-bold text-xs">
                      Precio de Venta al Cliente para Llevar ($ COP)
                    </label>
                    <span className="text-[10px] text-orange-400 font-mono font-bold">Cargo por empaque</span>
                  </div>
                  <input
                    type="number"
                    min="0"
                    step="100"
                    value={editPrecioVenta}
                    onChange={(e) => setEditPrecioVenta(parseFloat(e.target.value) || 0)}
                    placeholder="Ej: 1500 (para C1) o 500 (para P1) o 0"
                    className="w-full bg-slate-900 border border-orange-700/80 rounded-lg p-2 text-emerald-400 font-mono font-bold text-sm focus:outline-none"
                  />
                  <p className="text-[10px] text-orange-300/80 leading-tight">
                    💡 Si se incluye en la receta marcado como <strong>"Solo Llevar"</strong>, este precio se sumará automáticamente a la cuenta final cuando el pedido sea para llevar.
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-bold mb-1">Categoría</label>
                  <select
                    value={editCategoriaId}
                    onChange={(e) => setEditCategoriaId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="">(Sin categoría)</option>
                    {categorias.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.nombre}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-slate-400 font-bold mb-1">Unidad Base</label>
                  <input
                    type="text"
                    disabled
                    value={insumoEditando.unidad_base}
                    className="w-full bg-slate-950/60 border border-slate-800 rounded-xl p-2.5 text-slate-400 font-bold cursor-not-allowed"
                    title="La unidad base no se modifica para proteger las recetas calculadas"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-bold mb-1">
                    Costo / Precio Unitario ($ COP)
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 font-mono font-bold">$</span>
                    <input
                      type="number"
                      min="0"
                      step="any"
                      required
                      value={editCostoUnitario}
                      onChange={(e) => setEditCostoUnitario(parseFloat(e.target.value) || 0)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 pl-7 pr-3 text-emerald-400 font-mono font-bold text-sm focus:outline-none focus:border-purple-500"
                    />
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1">
                    Costo por cada 1 {insumoEditando.unidad_base}
                  </p>
                </div>

                <div>
                  <label className="block text-slate-400 font-bold mb-1">Stock Mínimo (Alerta)</label>
                  <input
                    type="number"
                    min="0"
                    step="any"
                    required
                    value={editStockMinimo}
                    onChange={(e) => setEditStockMinimo(parseFloat(e.target.value) || 0)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white font-mono font-bold focus:outline-none focus:border-purple-500"
                  />
                  <p className="text-[10px] text-slate-500 mt-1">
                    En {insumoEditando.unidad_base}
                  </p>
                </div>
              </div>

              <div className="p-3 bg-purple-950/30 border border-purple-900/50 rounded-xl text-[11px] text-purple-300">
                💡 <strong>Impacto en Recetas:</strong> Al actualizar el costo unitario de este insumo, se recalculará automáticamente el costo de preparación y margen de rentabilidad de todos los platos que lo contengan.
              </div>

              <div className="pt-3 flex justify-end gap-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setInsumoEditando(null)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-white cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={guardandoEdicion}
                  className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 font-bold text-white shadow-lg cursor-pointer"
                >
                  {guardandoEdicion ? 'Guardando...' : 'Guardar Cambios'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
