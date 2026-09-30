import React, { useState, useEffect } from 'react'
import { Navbar } from '../components/Navbar'
import {
  getDashboardApi,
  getReporteVentasApi,
  getComprasApi,
  crearCompraApi,
  getAuditoriaApi,
  getIngredientesApi,
  getPreparadosApi,
  descartarPreparadoApi,
  getRecetaProductoApi,
  guardarRecetaProductoApi,
  crearIngredienteApi,
  crearProductoApi,
  actualizarProductoApi,
  eliminarProductoApi,
} from '../api/admin'
import { getProductosApi, getCategoriasApi } from '../api/mesero'
import type {
  DashboardOut,
  ReporteVentasOut,
  CompraOut,
  HistorialAccionOut,
  IngredienteItem,
  PreparadoAdminItem,
  DetalleRecetaInput,
} from '../types/admin'
import type { Producto, Categoria } from '../types/mesero'
import { InventarioTab } from '../components/admin/InventarioTab'
import { UsuariosTab } from '../components/admin/UsuariosTab'
import { ConfiguracionTab } from '../components/admin/ConfiguracionTab'
import { AsistenciaTab } from '../components/admin/AsistenciaTab'
import {
  Shield,
  TrendingUp,
  DollarSign,
  ShoppingBag,
  AlertTriangle,
  RefreshCw,
  Award,
  Package,
  Truck,
  History,
  Clock,
  FileSpreadsheet,
  Plus,
  Trash2,
  CheckCircle2,
  Layers,
  Receipt,
  User,
  Users,
  UtensilsCrossed,
  Search,
  Save,
  X,
  Boxes,
  Settings,
  Pencil,
} from 'lucide-react'

type AdminTab = 'DASHBOARD' | 'PLANILLA' | 'INVENTARIO' | 'RECETAS' | 'COMPRAS' | 'PREPARADOS' | 'USUARIOS' | 'ASISTENCIA' | 'CONFIGURACION' | 'AUDITORIA'

export const Admin: React.FC = () => {
  const [tabActiva, setTabActiva] = useState<AdminTab>('DASHBOARD')

  // Estado Dashboard
  const [dashData, setDashData] = useState<DashboardOut | null>(null)
  const [dashLoading, setDashLoading] = useState(true)
  const [dashError, setDashError] = useState<string | null>(null)

  // Estado Planilla Diaria & Reportes
  const [fechaDesde, setFechaDesde] = useState<string>(() => {
    const d = new Date()
    d.setDate(d.getDate() - 7)
    return d.toISOString().split('T')[0]
  })
  const [fechaHasta, setFechaHasta] = useState<string>(() => {
    return new Date().toISOString().split('T')[0]
  })
  const [canalFiltro, setCanalFiltro] = useState<string>('TODOS')
  const [reporteData, setReporteData] = useState<ReporteVentasOut | null>(null)
  const [reporteLoading, setReporteLoading] = useState(false)

  // Estado Compras
  const [compras, setCompras] = useState<CompraOut[]>([])
  const [ingredientes, setIngredientes] = useState<IngredienteItem[]>([])
  const [comprasLoading, setComprasLoading] = useState(false)
  const [isNuevaCompraOpen, setIsNuevaCompraOpen] = useState(false)
  const [compraProveedor, setCompraProveedor] = useState('')
  const [compraDescripcion, setCompraDescripcion] = useState('')
  const [compraLineas, setCompraLineas] = useState<Array<{ ingrediente_id: number; cantidad: number; costo_unitario: number }>>([
    { ingrediente_id: 1, cantidad: 10, costo_unitario: 2500 },
  ])
  const [guardandoCompra, setGuardandoCompra] = useState(false)

  // Estado Auditoría
  const [auditoria, setAuditoria] = useState<HistorialAccionOut[]>([])
  const [auditoriaLoading, setAuditoriaLoading] = useState(false)
  const [filtroAccion, setFiltroAccion] = useState<string>('')

  // Estado Preparados
  const [preparados, setPreparados] = useState<PreparadoAdminItem[]>([])
  const [preparadosLoading, setPreparadosLoading] = useState(false)
  const [descartandoId, setDescartandoId] = useState<number | null>(null)
  const [motivoDescarte, setMotivoDescarte] = useState('Merma / Tiempo límite superado')

  // Estado Recetas del Menú
  const [productos, setProductos] = useState<Producto[]>([])
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [productoSeleccionado, setProductoSeleccionado] = useState<Producto | null>(null)
  const [recetaLineas, setRecetaLineas] = useState<DetalleRecetaInput[]>([])
  const [recetaLoading, setRecetaLoading] = useState(false)
  const [guardandoReceta, setGuardandoReceta] = useState(false)
  const [recetaError, setRecetaError] = useState<string | null>(null)
  const [busquedaReceta, setBusquedaReceta] = useState('')
  const [categoriaRecetaFiltro, setCategoriaRecetaFiltro] = useState<number | null>(null)

  // Modal nuevo ingrediente
  const [nuevoIngModalOpen, setNuevoIngModalOpen] = useState(false)
  const [nuevoIngNombre, setNuevoIngNombre] = useState('')
  const [nuevoIngUnidad, setNuevoIngUnidad] = useState('UNIDAD')
  const [nuevoIngCosto, setNuevoIngCosto] = useState(1000)
  const [nuevoIngStock, setNuevoIngStock] = useState(50)
  const [creandoIngrediente, setCreandoIngrediente] = useState(false)

  // Modal nuevo producto
  const [nuevoProdModalOpen, setNuevoProdModalOpen] = useState(false)
  const [nuevoProdNombre, setNuevoProdNombre] = useState('')
  const [nuevoProdCategoriaId, setNuevoProdCategoriaId] = useState<number | ''>('')
  const [nuevoProdPrecio, setNuevoProdPrecio] = useState<number>(22000)
  const [nuevoProdDescripcion, setNuevoProdDescripcion] = useState('')
  const [creandoProducto, setCreandoProducto] = useState(false)

  // Modal editar producto (precio / nombre / descripcion)
  const [editarProdModalOpen, setEditarProdModalOpen] = useState(false)
  const [editarProdNombre, setEditarProdNombre] = useState('')
  const [editarProdPrecio, setEditarProdPrecio] = useState<number>(0)
  const [editarProdDescripcion, setEditarProdDescripcion] = useState('')
  const [editarProdCategoriaId, setEditarProdCategoriaId] = useState<number | ''>('')
  const [guardandoEdicionProd, setGuardandoEdicionProd] = useState(false)
  const [eliminandoProducto, setEliminandoProducto] = useState(false)

  // Feedback general
  const [bannerSuccess, setBannerSuccess] = useState<string | null>(null)

  // 1. Cargar Dashboard
  const cargarDashboard = async () => {
    setDashLoading(true)
    setDashError(null)
    try {
      const data = await getDashboardApi()
      setDashData(data)
    } catch (err: any) {
      setDashError(err.response?.data?.detail || 'Error al conectar con el servidor')
    } finally {
      setDashLoading(false)
    }
  }

  // 2. Cargar Reporte
  const cargarReporte = async () => {
    setReporteLoading(true)
    try {
      const data = await getReporteVentasApi(fechaDesde, fechaHasta, canalFiltro)
      setReporteData(data)
    } catch (err: any) {
      console.error('Error cargando reportes:', err)
    } finally {
      setReporteLoading(false)
    }
  }

  // 3. Cargar Compras e Ingredientes
  const cargarCompras = async () => {
    setComprasLoading(true)
    try {
      const [c, ing] = await Promise.all([getComprasApi(), getIngredientesApi()])
      setCompras(c)
      setIngredientes(ing)
    } catch (err: any) {
      console.error('Error cargando compras:', err)
    } finally {
      setComprasLoading(false)
    }
  }

  // 4. Cargar Auditoría
  const cargarAuditoria = async () => {
    setAuditoriaLoading(true)
    try {
      const data = await getAuditoriaApi({ accion: filtroAccion || undefined, limit: 100 })
      setAuditoria(data)
    } catch (err: any) {
      console.error('Error cargando auditoría:', err)
    } finally {
      setAuditoriaLoading(false)
    }
  }

  // 5. Cargar Preparados
  const cargarPreparados = async () => {
    setPreparadosLoading(true)
    try {
      const data = await getPreparadosApi('DISPONIBLE')
      setPreparados(data)
    } catch (err: any) {
      console.error('Error cargando preparados:', err)
    } finally {
      setPreparadosLoading(false)
    }
  }

  // 6. Cargar Productos y Recetas
  const cargarProductosYRecetas = async () => {
    setRecetaLoading(true)
    try {
      const [prods, cats, ings] = await Promise.all([
        getProductosApi(),
        getCategoriasApi(),
        getIngredientesApi(),
      ])
      setProductos(prods)
      setCategorias(cats)
      setIngredientes(ings)

      if (productoSeleccionado) {
        const actualizado = prods.find((p) => p.id === productoSeleccionado.id)
        if (actualizado) {
          setProductoSeleccionado(actualizado)
          const lineas = await getRecetaProductoApi(actualizado.id)
          setRecetaLineas(
            lineas.map((l) => ({
              ingrediente_id: l.ingrediente_id,
              cantidad: Number(l.cantidad),
              unidad: l.unidad,
            }))
          )
        }
      } else if (prods.length > 0) {
        // Seleccionar por defecto el primer producto
        const primerComida = prods.find((p) => p.es_cocina !== false) || prods[0]
        setProductoSeleccionado(primerComida)
        const lineas = await getRecetaProductoApi(primerComida.id)
        setRecetaLineas(
          lineas.map((l) => ({
            ingrediente_id: l.ingrediente_id,
            cantidad: Number(l.cantidad),
            unidad: l.unidad,
          }))
        )
      }
    } catch (err) {
      console.error('Error cargando recetas y catálogo:', err)
    } finally {
      setRecetaLoading(false)
    }
  }

  const handleSeleccionarProducto = async (prod: Producto) => {
    setProductoSeleccionado(prod)
    setRecetaLoading(true)
    setRecetaError(null)
    try {
      const lineas = await getRecetaProductoApi(prod.id)
      setRecetaLineas(
        lineas.map((l) => ({
          ingrediente_id: l.ingrediente_id,
          cantidad: Number(l.cantidad),
          unidad: l.unidad,
        }))
      )
    } catch (err: any) {
      setRecetaError(err.response?.data?.detail || 'Error al cargar receta')
      setRecetaLineas([])
    } finally {
      setRecetaLoading(false)
    }
  }

  const handleAgregarLineaReceta = () => {
    if (ingredientes.length === 0) return
    const primerIng = ingredientes[0]
    setRecetaLineas((prev) => [
      ...prev,
      {
        ingrediente_id: primerIng.id,
        cantidad: 1,
        unidad: primerIng.unidad_base === 'GRAMO' ? 'g' : primerIng.unidad_base === 'MILILITRO' ? 'ml' : 'u',
      },
    ])
  }

  const handleEliminarLineaReceta = (idx: number) => {
    setRecetaLineas((prev) => prev.filter((_, i) => i !== idx))
  }

  const handleModificarLineaReceta = (idx: number, campo: keyof DetalleRecetaInput, valor: any) => {
    setRecetaLineas((prev) => {
      const copia = [...prev]
      copia[idx] = { ...copia[idx], [campo]: valor }
      if (campo === 'ingrediente_id') {
        const ing = ingredientes.find((i) => i.id === Number(valor))
        if (ing) {
          copia[idx].unidad = ing.unidad_base === 'GRAMO' ? 'g' : ing.unidad_base === 'MILILITRO' ? 'ml' : 'u'
        }
      }
      return copia
    })
  }

  const handleGuardarReceta = async () => {
    if (!productoSeleccionado) return
    setGuardandoReceta(true)
    setRecetaError(null)
    try {
      await guardarRecetaProductoApi(productoSeleccionado.id, recetaLineas)
      setBannerSuccess(
        `✓ ¡Receta de "${productoSeleccionado.nombre}" guardada! Los ingredientes han sido sincronizados para la comanda y cocina.`
      )
      setTimeout(() => setBannerSuccess(null), 5000)
      await cargarProductosYRecetas()
    } catch (err: any) {
      setRecetaError(err.response?.data?.detail || 'Error al guardar la receta')
    } finally {
      setGuardandoReceta(false)
    }
  }

  const handleCrearNuevoIngrediente = async () => {
    if (!nuevoIngNombre.trim()) return
    setCreandoIngrediente(true)
    try {
      const nuevo = await crearIngredienteApi({
        nombre: nuevoIngNombre.trim(),
        unidad_base: nuevoIngUnidad,
        costo_unitario: nuevoIngCosto,
        stock_actual: nuevoIngStock,
      })
      setIngredientes((prev) => [...prev, nuevo])
      setRecetaLineas((prev) => [
        ...prev,
        {
          ingrediente_id: nuevo.id,
          cantidad: 1,
          unidad: nuevo.unidad_base === 'GRAMO' ? 'g' : nuevo.unidad_base === 'MILILITRO' ? 'ml' : 'u',
        },
      ])
      setNuevoIngModalOpen(false)
      setNuevoIngNombre('')
      setBannerSuccess(`✓ Ingrediente "${nuevo.nombre}" creado y añadido a la receta.`)
      setTimeout(() => setBannerSuccess(null), 4000)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al crear ingrediente')
    } finally {
      setCreandoIngrediente(false)
    }
  }

  const handleAbrirEditarProducto = (prod: Producto) => {
    setEditarProdNombre(prod.nombre)
    setEditarProdPrecio(Number(prod.precio || 0))
    setEditarProdDescripcion(prod.descripcion || '')
    setEditarProdCategoriaId(prod.categoria_id)
    setEditarProdModalOpen(true)
  }

  const handleGuardarEditarProducto = async () => {
    if (!productoSeleccionado) return
    if (!editarProdNombre.trim()) {
      alert('El nombre del producto no puede estar vacío')
      return
    }
    if (editarProdPrecio < 0) {
      alert('El precio no puede ser negativo')
      return
    }
    setGuardandoEdicionProd(true)
    try {
      const prodActualizado = await actualizarProductoApi(productoSeleccionado.id, {
        nombre: editarProdNombre.trim(),
        precio: Number(editarProdPrecio),
        descripcion: editarProdDescripcion.trim(),
        categoria_id: editarProdCategoriaId ? Number(editarProdCategoriaId) : undefined,
      })
      setProductoSeleccionado(prodActualizado)
      setBannerSuccess(
        `✓ ¡Producto "${prodActualizado.nombre}" actualizado con éxito! Nuevo precio: $${Number(
          prodActualizado.precio || 0
        ).toLocaleString('es-CO')}`
      )
      setTimeout(() => setBannerSuccess(null), 5000)
      setEditarProdModalOpen(false)
      await cargarProductosYRecetas()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al actualizar el producto')
    } finally {
      setGuardandoEdicionProd(false)
    }
  }

  const handleCrearNuevoProducto = async () => {
    if (!nuevoProdNombre.trim()) {
      alert('Por favor escribe el nombre del plato / hamburguesa')
      return
    }
    if (!nuevoProdCategoriaId) {
      alert('Por favor selecciona una categoría')
      return
    }
    if (nuevoProdPrecio < 0) {
      alert('El precio no puede ser negativo')
      return
    }
    setCreandoProducto(true)
    try {
      const nuevo = await crearProductoApi({
        nombre: nuevoProdNombre.trim(),
        categoria_id: Number(nuevoProdCategoriaId),
        precio: Number(nuevoProdPrecio),
        descripcion: nuevoProdDescripcion.trim() || undefined,
        iva_incluido: true,
      })
      setBannerSuccess(`✓ ¡Plato "${nuevo.nombre}" creado exitosamente! Ahora puedes definir sus ingredientes y receta.`)
      setTimeout(() => setBannerSuccess(null), 6000)
      setNuevoProdModalOpen(false)
      setNuevoProdNombre('')
      setNuevoProdDescripcion('')
      setNuevoProdPrecio(22000)
      await cargarProductosYRecetas()
      setProductoSeleccionado(nuevo)
      handleSeleccionarProducto(nuevo)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al crear el producto')
    } finally {
      setCreandoProducto(false)
    }
  }

  const handleDesactivarProducto = async () => {
    if (!productoSeleccionado) return
    const confirma = window.confirm(
      `¿Estás seguro de que deseas desactivar "${productoSeleccionado.nombre}" del menú?\n\nEl producto dejará de aparecer para los meseros inmediatamente, pero se conservará su historial para reportes de ventas.`
    )
    if (!confirma) return
    setEliminandoProducto(true)
    try {
      await eliminarProductoApi(productoSeleccionado.id)
      setBannerSuccess(`✓ "${productoSeleccionado.nombre}" ha sido desactivado del menú.`)
      setTimeout(() => setBannerSuccess(null), 5000)
      setProductoSeleccionado(null)
      setRecetaLineas([])
      await cargarProductosYRecetas()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al desactivar el producto')
    } finally {
      setEliminandoProducto(false)
    }
  }

  useEffect(() => {
    cargarDashboard()
  }, [])

  useEffect(() => {
    if (tabActiva === 'PLANILLA') cargarReporte()
    if (tabActiva === 'COMPRAS') cargarCompras()
    if (tabActiva === 'AUDITORIA') cargarAuditoria()
    if (tabActiva === 'PREPARADOS') cargarPreparados()
    if (tabActiva === 'RECETAS') cargarProductosYRecetas()
  }, [tabActiva])

  // Manejar Registro de Compra
  const handleGuardarCompra = async (e: React.FormEvent) => {
    e.preventDefault()
    if (compraLineas.length === 0) return

    setGuardandoCompra(true)
    try {
      await crearCompraApi({
        descripcion: `${compraProveedor ? `Proveedor: ${compraProveedor}. ` : ''}${compraDescripcion}`.trim(),
        detalles: compraLineas.map((l) => ({
          ingrediente_id: Number(l.ingrediente_id),
          cantidad: Number(l.cantidad),
          costo_unitario: Number(l.costo_unitario),
        })),
      })
      setBannerSuccess('✓ Compra de insumos registrada exitosamente. Inventario reabastecido.')
      setIsNuevaCompraOpen(false)
      setCompraDescripcion('')
      setCompraProveedor('')
      cargarCompras()
      cargarDashboard()
      setTimeout(() => setBannerSuccess(null), 4000)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al registrar la compra')
    } finally {
      setGuardandoCompra(false)
    }
  }

  // Manejar Descarte de Preparado
  const handleConfirmarDescarte = async (id: number) => {
    try {
      await descartarPreparadoApi(id, motivoDescarte)
      setBannerSuccess('✓ Preparado descartado y registrado como merma en auditoría.')
      setDescartandoId(null)
      cargarPreparados()
      cargarDashboard()
      setTimeout(() => setBannerSuccess(null), 4000)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al descartar preparado')
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col selection:bg-purple-600 selection:text-white">
      <Navbar title="Centro de Mando • Administración & Dueño Mr. Burger" />

      <main className="flex-1 p-2.5 sm:p-4 max-w-6xl mx-auto w-full min-w-0 flex flex-col overflow-x-hidden">
        {/* Cabecera del Panel */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-purple-950/70 via-slate-900 to-slate-900 border border-purple-800/40 rounded-2xl p-4 sm:p-5 mb-5 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-purple-600/30 border border-purple-500/50 flex items-center justify-center text-purple-400 shrink-0">
              <Shield className="w-5 h-5 sm:w-6 sm:h-6" />
            </div>
            <div className="min-w-0">
              <h1 className="text-lg sm:text-xl font-black text-white uppercase tracking-wide truncate">
                Panel Gerencial Ejecutivo
              </h1>
              <p className="text-[11px] sm:text-xs text-slate-400 truncate">
                Gobernanza completa: Ventas en vivo, Cuadre diario, Reabastecimiento y Auditoría
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (tabActiva === 'DASHBOARD') cargarDashboard()
                if (tabActiva === 'PLANILLA') cargarReporte()
                if (tabActiva === 'COMPRAS') cargarCompras()
                if (tabActiva === 'RECETAS') cargarProductosYRecetas()
                if (tabActiva === 'AUDITORIA') cargarAuditoria()
                if (tabActiva === 'PREPARADOS') cargarPreparados()
              }}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-200 transition cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${dashLoading || reporteLoading || comprasLoading || auditoriaLoading || preparadosLoading || recetaLoading ? 'animate-spin' : ''}`} />
              <span>Actualizar</span>
            </button>
          </div>
        </div>

        {/* Notificación de éxito */}
        {bannerSuccess && (
          <div className="mb-4 p-3 bg-emerald-950/80 border border-emerald-700 rounded-xl text-emerald-200 text-xs flex items-center gap-2 animate-fade-in">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{bannerSuccess}</span>
          </div>
        )}

        {/* Selector de Pestañas Principales (Deslizable horizontalmente en móviles) */}
        <div className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto pb-2.5 mb-5 max-w-full scrollbar-thin scrollbar-thumb-purple-900/40">
          <button
            onClick={() => setTabActiva('DASHBOARD')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
              tabActiva === 'DASHBOARD'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-950/50'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            <span>Dashboard Ejecutivo</span>
          </button>

          <button
            onClick={() => setTabActiva('PLANILLA')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
              tabActiva === 'PLANILLA'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-950/50'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <FileSpreadsheet className="w-4 h-4" />
            <span>Planilla Diaria & Reportes</span>
          </button>

          <button
            onClick={() => setTabActiva('INVENTARIO')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
              tabActiva === 'INVENTARIO'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-950/50'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <Boxes className="w-4 h-4" />
            <span>Inventario & Materias Primas</span>
          </button>

          <button
            onClick={() => setTabActiva('RECETAS')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
              tabActiva === 'RECETAS'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-950/50'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <UtensilsCrossed className="w-4 h-4" />
            <span>Recetas del Menú</span>
          </button>

          <button
            onClick={() => setTabActiva('COMPRAS')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
              tabActiva === 'COMPRAS'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-950/50'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <Truck className="w-4 h-4" />
            <span>Compras & Proveedores</span>
          </button>

          <button
            onClick={() => setTabActiva('PREPARADOS')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
              tabActiva === 'PREPARADOS'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-950/50'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <Package className="w-4 h-4" />
            <span>Bolsa de Preparados ({dashData?.preparados_disponibles_count || 0})</span>
          </button>

          <button
            onClick={() => setTabActiva('USUARIOS')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
              tabActiva === 'USUARIOS'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-950/50'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Equipo & Seguridad</span>
          </button>

          <button
            onClick={() => setTabActiva('ASISTENCIA')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
              tabActiva === 'ASISTENCIA'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-950/50'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <Clock className="w-4 h-4" />
            <span>Asistencia & Turnos</span>
          </button>

          <button
            onClick={() => setTabActiva('CONFIGURACION')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
              tabActiva === 'CONFIGURACION'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-950/50'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <Settings className="w-4 h-4" />
            <span>Configuración</span>
          </button>

          <button
            onClick={() => setTabActiva('AUDITORIA')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
              tabActiva === 'AUDITORIA'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-950/50'
                : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <History className="w-4 h-4" />
            <span>Bitácora de Auditoría</span>
          </button>
        </div>

        {/* ======================================================== */}
        {/* PESTAÑA 1: DASHBOARD EJECUTIVO */}
        {/* ======================================================== */}
        {tabActiva === 'DASHBOARD' && (
          <div className="space-y-6 animate-fade-in">
            {dashError && (
              <div className="p-4 bg-red-950/70 border border-red-800 rounded-xl text-red-200 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                <span>{dashError}</span>
              </div>
            )}

            {/* Tarjetas de Métricas Principales (KPIs) */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-4">
              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-3 sm:p-4 min-w-0 overflow-hidden flex flex-col justify-between">
                <div className="flex items-center justify-between text-slate-400 mb-2 gap-1">
                  <span className="text-xs font-bold uppercase tracking-wider truncate">Ventas Hoy</span>
                  <div className="w-7 h-7 rounded-lg bg-emerald-600/20 text-emerald-400 flex items-center justify-center shrink-0">
                    <DollarSign className="w-4 h-4" />
                  </div>
                </div>
                <p className="text-base sm:text-xl md:text-2xl font-black text-emerald-400 truncate" title={`$${dashData ? Number(dashData.total_ventas).toLocaleString('es-CO') : '0'}`}>
                  ${dashData ? Number(dashData.total_ventas).toLocaleString('es-CO') : '0'}
                </p>
                <p className="text-[10px] sm:text-[11px] text-slate-500 mt-1 truncate">Cuentas cerradas</p>
              </div>

              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-3 sm:p-4 min-w-0 overflow-hidden flex flex-col justify-between">
                <div className="flex items-center justify-between text-slate-400 mb-2 gap-1">
                  <span className="text-xs font-bold uppercase tracking-wider truncate">Pedidos Hoy</span>
                  <div className="w-7 h-7 rounded-lg bg-blue-600/20 text-blue-400 flex items-center justify-center shrink-0">
                    <ShoppingBag className="w-4 h-4" />
                  </div>
                </div>
                <p className="text-base sm:text-xl md:text-2xl font-black text-white truncate">
                  {dashData ? dashData.total_pedidos : '0'}
                </p>
                <p className="text-[10px] sm:text-[11px] text-slate-500 mt-1 truncate">Comandas procesadas</p>
              </div>

              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-3 sm:p-4 min-w-0 overflow-hidden flex flex-col justify-between">
                <div className="flex items-center justify-between text-slate-400 mb-2 gap-1">
                  <span className="text-xs font-bold uppercase tracking-wider truncate">Ticket Promedio</span>
                  <div className="w-7 h-7 rounded-lg bg-purple-600/20 text-purple-400 flex items-center justify-center shrink-0">
                    <TrendingUp className="w-4 h-4" />
                  </div>
                </div>
                <p className="text-base sm:text-xl md:text-2xl font-black text-purple-300 truncate" title={`$${dashData ? Number(dashData.ticket_promedio).toLocaleString('es-CO') : '0'}`}>
                  ${dashData ? Number(dashData.ticket_promedio).toLocaleString('es-CO') : '0'}
                </p>
                <p className="text-[10px] sm:text-[11px] text-slate-500 mt-1 truncate">Gasto medio por orden</p>
              </div>

              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-3 sm:p-4 min-w-0 overflow-hidden flex flex-col justify-between">
                <div className="flex items-center justify-between text-slate-400 mb-2 gap-1">
                  <span className="text-xs font-bold uppercase tracking-wider truncate">Bolsa Preparados</span>
                  <div className="w-7 h-7 rounded-lg bg-amber-600/20 text-amber-400 flex items-center justify-center shrink-0">
                    <Package className="w-4 h-4" />
                  </div>
                </div>
                <p className="text-base sm:text-xl md:text-2xl font-black text-amber-400 truncate">
                  {dashData ? dashData.preparados_disponibles_count : '0'}
                </p>
                <p className="text-[10px] sm:text-[11px] text-slate-500 mt-1 truncate">Listos para reventa</p>
              </div>
            </div>

            {/* Sección de Canales y Formas de Pago */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
              {/* Ventas por Canal */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-3.5 sm:p-5 min-w-0 overflow-hidden">
                <h3 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-purple-400 shrink-0" />
                  <span className="truncate">Ventas de Hoy por Canal</span>
                </h3>
                <div className="space-y-3">
                  {dashData && dashData.ventas_por_canal ? (
                    Object.entries(dashData.ventas_por_canal).map(([canal, monto]) => (
                      <div key={canal} className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs gap-2 min-w-0">
                        <span className="font-bold text-slate-200 uppercase truncate">{canal}</span>
                        <span className="font-mono font-bold text-emerald-400 shrink-0">
                          ${Number(monto).toLocaleString('es-CO')}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-slate-500">Sin datos registrados hoy</div>
                  )}
                </div>
              </div>

              {/* Formas de Pago */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-3.5 sm:p-5 min-w-0 overflow-hidden">
                <h3 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
                  <Receipt className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span className="truncate">Recaudos de Hoy por Forma de Pago</span>
                </h3>
                <div className="space-y-3">
                  {dashData && dashData.pagos_por_metodo ? (
                    Object.entries(dashData.pagos_por_metodo).map(([metodo, monto]) => (
                      <div key={metodo} className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs gap-2 min-w-0">
                        <span className="font-semibold text-slate-300 truncate">{metodo}</span>
                        <span className="font-mono font-bold text-slate-100 shrink-0">
                          ${Number(monto).toLocaleString('es-CO')}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-slate-500">Sin cobros registrados hoy</div>
                  )}
                </div>
              </div>
            </div>

            {/* Top Productos y Stock Crítico */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
              {/* Top Productos */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-3.5 sm:p-5 min-w-0 overflow-hidden">
                <h3 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
                  <Award className="w-4 h-4 text-orange-400 shrink-0" />
                  <span className="truncate">Top Productos Más Vendidos Hoy</span>
                </h3>
                {dashData && dashData.top_productos.length > 0 ? (
                  <div className="space-y-3">
                    {dashData.top_productos.map((prod, idx) => (
                      <div
                        key={prod.producto_id}
                        className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs gap-2 min-w-0"
                      >
                        <div className="flex items-center gap-2.5 sm:gap-3 min-w-0">
                          <span className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center font-bold text-slate-300 shrink-0">
                            #{idx + 1}
                          </span>
                          <div className="min-w-0">
                            <p className="font-bold text-slate-100 truncate">{prod.nombre}</p>
                            <p className="text-slate-400 truncate">{prod.cantidad} unidades</p>
                          </div>
                        </div>
                        <span className="font-mono font-bold text-emerald-400 shrink-0">
                          ${Number(prod.total).toLocaleString('es-CO')}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-500 text-xs">
                    Aún no hay ventas cerradas registradas en el día de hoy.
                  </div>
                )}
              </div>

              {/* Alertas de Stock Crítico */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-3.5 sm:p-5 min-w-0 overflow-hidden">
                <h3 className="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                  <span className="truncate">Alertas de Stock Crítico</span>
                </h3>
                {dashData && dashData.alertas_stock.length > 0 ? (
                  <div className="space-y-3">
                    {dashData.alertas_stock.map((alerta) => (
                      <div
                        key={alerta.ingrediente_id}
                        className="flex items-center justify-between p-3 rounded-xl bg-amber-950/20 border border-amber-800/40 text-xs gap-2 min-w-0"
                      >
                        <div className="min-w-0">
                          <p className="font-bold text-amber-200 truncate">{alerta.nombre}</p>
                          <p className="text-slate-400 truncate">
                            Mínimo: {alerta.stock_minimo} {alerta.unidad_base} • Déficit: {alerta.deficit}
                          </p>
                        </div>
                        <span className="font-mono font-bold text-red-400 bg-red-950/60 px-2 py-1 rounded border border-red-800/60 shrink-0">
                          Quedan: {alerta.stock_actual}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-500 text-xs">
                    ✓ Todos los insumos e ingredientes cuentan con stock óptimo.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* PESTAÑA 2: PLANILLA DIARIA MR. BURGER & REPORTES */}
        {/* ======================================================== */}
        {tabActiva === 'PLANILLA' && (
          <div className="space-y-6 animate-fade-in">
            {/* Filtros de Fecha y Canal */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400 font-bold">Desde:</span>
                <input
                  type="date"
                  value={fechaDesde}
                  onChange={(e) => setFechaDesde(e.target.value)}
                  className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white font-mono text-xs focus:outline-none"
                />
              </div>

              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400 font-bold">Hasta:</span>
                <input
                  type="date"
                  value={fechaHasta}
                  onChange={(e) => setFechaHasta(e.target.value)}
                  className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white font-mono text-xs focus:outline-none"
                />
              </div>

              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400 font-bold">Canal:</span>
                <select
                  value={canalFiltro}
                  onChange={(e) => setCanalFiltro(e.target.value)}
                  className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-white text-xs focus:outline-none"
                >
                  <option value="TODOS">Todos los Canales</option>
                  <option value="MESA">Mesas</option>
                  <option value="MOSTRADOR">Mostrador</option>
                  <option value="DOMICILIO">Domicilio</option>
                  <option value="DIDI">DiDi Food</option>
                </select>
              </div>

              <button
                onClick={cargarReporte}
                disabled={reporteLoading}
                className="px-4 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-bold transition cursor-pointer"
              >
                Generar Cuadre
              </button>
            </div>

            {/* Réplica Digital de la Planilla Manual Mr. Burger */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
              <div className="border-b border-slate-800 pb-4 mb-4 flex justify-between items-center">
                <div>
                  <h2 className="text-base font-black text-white flex items-center gap-2">
                    <FileSpreadsheet className="w-5 h-5 text-amber-400" />
                    Planilla Oficial de Cuadre Diario • Mr. Burger Cali
                  </h2>
                  <p className="text-xs text-slate-400">
                    Fórmula Contable: Base Inicial + Ventas Totales - Compras Insumos - Gastos Menores = Efectivo en Cajón
                  </p>
                </div>
                <button
                  onClick={() => window.print()}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold transition cursor-pointer"
                >
                  Imprimir Planilla
                </button>
              </div>

              {/* Resumen Financiero del Período */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-6">
                <div className="p-3 sm:p-4 rounded-xl bg-slate-950 border border-slate-800 min-w-0 overflow-hidden">
                  <span className="text-xs text-slate-400 font-bold uppercase truncate block">Ventas Período</span>
                  <p className="text-lg sm:text-xl font-black text-emerald-400 mt-1 truncate" title={`$${reporteData ? Number(reporteData.total_ventas).toLocaleString('es-CO') : '0'}`}>
                    ${reporteData ? Number(reporteData.total_ventas).toLocaleString('es-CO') : '0'}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5 truncate">{reporteData?.total_pedidos || 0} pedidos atendidos</p>
                </div>

                <div className="p-3 sm:p-4 rounded-xl bg-slate-950 border border-slate-800 min-w-0 overflow-hidden">
                  <span className="text-xs text-slate-400 font-bold uppercase truncate block">Ticket Promedio</span>
                  <p className="text-lg sm:text-xl font-black text-purple-300 mt-1 truncate" title={`$${reporteData ? Number(reporteData.ticket_promedio).toLocaleString('es-CO') : '0'}`}>
                    ${reporteData ? Number(reporteData.ticket_promedio).toLocaleString('es-CO') : '0'}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5 truncate">Media de consumo por cliente</p>
                </div>

                <div className="p-3 sm:p-4 rounded-xl bg-slate-950 border border-slate-800 min-w-0 overflow-hidden">
                  <span className="text-xs text-slate-400 font-bold uppercase truncate block">Régimen Tributario</span>
                  <p className="text-base sm:text-lg font-black text-sky-400 mt-1 truncate" title="No Responsable de IVA (Art. 512-13 E.T.)">
                    No Responsable
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5 truncate">Art. 512-13 E.T. • Tarifa 0%</p>
                </div>
              </div>

              {/* Tabla de Desglose Día por Día */}
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 font-bold uppercase">
                    <tr>
                      <th className="p-3">Fecha</th>
                      <th className="p-3 text-center">Pedidos</th>
                      <th className="p-3 text-right">Subtotal</th>
                      <th className="p-3 text-right">Impuesto (0%)</th>
                      <th className="p-3 text-right">Total Facturado</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {reporteData && reporteData.desglose_diario && reporteData.desglose_diario.length > 0 ? (
                      reporteData.desglose_diario.map((dia) => (
                        <tr key={dia.fecha} className="hover:bg-slate-800/40 transition">
                          <td className="p-3 font-mono font-bold text-slate-200">{dia.fecha}</td>
                          <td className="p-3 text-center font-semibold text-slate-300">{dia.pedidos_count}</td>
                          <td className="p-3 text-right font-mono text-slate-400">${Number(dia.subtotal).toLocaleString('es-CO')}</td>
                          <td className="p-3 text-right font-mono text-slate-400">${Number(dia.iva).toLocaleString('es-CO')}</td>
                          <td className="p-3 text-right font-mono font-bold text-emerald-400">${Number(dia.total).toLocaleString('es-CO')}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="text-center py-6 text-slate-500 text-xs">
                          No hay operaciones registradas en el rango seleccionado.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* PESTAÑA: INVENTARIO & MATERIAS PRIMAS */}
        {/* ======================================================== */}
        {tabActiva === 'INVENTARIO' && <InventarioTab />}

        {/* ======================================================== */}
        {/* PESTAÑA 3: COMPRAS A PROVEEDORES */}
        {/* ======================================================== */}
        {tabActiva === 'COMPRAS' && (
          <div className="space-y-6 animate-fade-in">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Truck className="w-5 h-5 text-sky-400" />
                  Compras de Insumos & Reabastecimiento
                </h2>
                <p className="text-xs text-slate-400">
                  Registra compras de pan, carne, verduras y salsas. El stock y el costo se recalculan automáticamente.
                </p>
              </div>

              <button
                onClick={() => setIsNuevaCompraOpen(true)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-lg transition cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                <span>Registrar Factura de Compra</span>
              </button>
            </div>

            {/* Modal de Nueva Compra */}
            {isNuevaCompraOpen && (
              <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
                <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-xl overflow-hidden shadow-2xl p-5 max-h-[90vh] overflow-y-auto">
                  <h3 className="text-sm font-black text-white uppercase mb-3 flex items-center gap-2">
                    <Truck className="w-4 h-4 text-sky-400" />
                    Registrar Factura de Proveedor
                  </h3>

                  <form onSubmit={handleGuardarCompra} className="space-y-4 text-xs">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-slate-400 font-bold mb-1">Proveedor / Razón Social:</label>
                        <input
                          type="text"
                          required
                          value={compraProveedor}
                          onChange={(e) => setCompraProveedor(e.target.value)}
                          placeholder="Ej. Panadería Central, Carnes Cali..."
                          className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-slate-400 font-bold mb-1"># Factura / Remisión:</label>
                        <input
                          type="text"
                          value={compraDescripcion}
                          onChange={(e) => setCompraDescripcion(e.target.value)}
                          placeholder="Ej. Factura #4092"
                          className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white focus:outline-none"
                        />
                      </div>
                    </div>

                    <div className="border-t border-slate-800 pt-3">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-bold text-slate-300">Insumos a Ingresar:</span>
                        <button
                          type="button"
                          onClick={() => setCompraLineas([...compraLineas, { ingrediente_id: ingredientes[0]?.id || 1, cantidad: 5, costo_unitario: 2000 }])}
                          className="text-purple-400 hover:text-purple-300 font-bold text-xs cursor-pointer"
                        >
                          + Agregar Insumo
                        </button>
                      </div>

                      <div className="space-y-2">
                        {compraLineas.map((linea, idx) => (
                          <div key={idx} className="grid grid-cols-12 gap-2 items-center bg-slate-950 p-2 rounded-lg border border-slate-800">
                            <div className="col-span-5">
                              <select
                                value={linea.ingrediente_id}
                                onChange={(e) => {
                                  const n = [...compraLineas]
                                  n[idx].ingrediente_id = Number(e.target.value)
                                  setCompraLineas(n)
                                }}
                                className="w-full bg-slate-900 border border-slate-700 rounded p-1 text-slate-200 text-xs"
                              >
                                {ingredientes.map((ing) => (
                                  <option key={ing.id} value={ing.id}>
                                    {ing.nombre} ({ing.unidad_base})
                                  </option>
                                ))}
                              </select>
                            </div>

                            <div className="col-span-3">
                              <input
                                type="number"
                                min="0.1"
                                step="0.1"
                                value={linea.cantidad}
                                onChange={(e) => {
                                  const n = [...compraLineas]
                                  n[idx].cantidad = Number(e.target.value)
                                  setCompraLineas(n)
                                }}
                                placeholder="Cant"
                                className="w-full bg-slate-900 border border-slate-700 rounded p-1 text-white font-mono text-xs text-center"
                              />
                            </div>

                            <div className="col-span-3">
                              <input
                                type="number"
                                min="0"
                                value={linea.costo_unitario}
                                onChange={(e) => {
                                  const n = [...compraLineas]
                                  n[idx].costo_unitario = Number(e.target.value)
                                  setCompraLineas(n)
                                }}
                                placeholder="Costo Unit"
                                className="w-full bg-slate-900 border border-slate-700 rounded p-1 text-emerald-400 font-mono text-xs text-right"
                              />
                            </div>

                            <div className="col-span-1 text-center">
                              {compraLineas.length > 1 && (
                                <button
                                  type="button"
                                  onClick={() => setCompraLineas(compraLineas.filter((_, i) => i !== idx))}
                                  className="text-red-400 hover:text-red-300"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex justify-between font-bold text-sm">
                      <span className="text-slate-400">Total Factura:</span>
                      <span className="text-emerald-400 font-mono">
                        ${compraLineas.reduce((acc, l) => acc + l.cantidad * l.costo_unitario, 0).toLocaleString('es-CO')} COP
                      </span>
                    </div>

                    <div className="flex justify-end gap-2 pt-2">
                      <button
                        type="button"
                        onClick={() => setIsNuevaCompraOpen(false)}
                        className="px-4 py-2 rounded-xl text-slate-400 hover:text-white cursor-pointer"
                      >
                        Cancelar
                      </button>
                      <button
                        type="submit"
                        disabled={guardandoCompra}
                        className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 font-bold text-white shadow-lg cursor-pointer"
                      >
                        {guardandoCompra ? 'Guardando...' : 'Confirmar e Ingresar a Stock'}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {/* Listado de Compras Previas */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 font-bold uppercase">
                  <tr>
                    <th className="p-3">Fecha</th>
                    <th className="p-3">Detalle / Proveedor</th>
                    <th className="p-3">Insumos Comprados</th>
                    <th className="p-3 text-right">Total Factura</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {compras.length > 0 ? (
                    compras.map((c) => (
                      <tr key={c.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3 font-mono text-slate-400">{new Date(c.creado_en).toLocaleString('es-CO')}</td>
                        <td className="p-3 font-semibold text-slate-200">{c.descripcion || 'Sin descripción'}</td>
                        <td className="p-3 text-slate-300">
                          {c.detalles.map((d) => `${d.cantidad}x ${d.ingrediente_nombre || 'Insumo'}`).join(', ')}
                        </td>
                        <td className="p-3 text-right font-mono font-bold text-emerald-400">
                          ${Number(c.costo_total).toLocaleString('es-CO')}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="text-center py-6 text-slate-500 text-xs">
                        No hay compras registradas en el historial.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* PESTAÑA 4: BOLSA DE PREPARADOS */}
        {/* ======================================================== */}
        {tabActiva === 'PREPARADOS' && (
          <div className="space-y-6 animate-fade-in">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Package className="w-5 h-5 text-amber-400" />
                Bolsa de Preparados (Reventa de Producidos Cancelados)
              </h2>
              <p className="text-xs text-slate-400">
                Alimentos ya cocinados de pedidos cancelados. Disponibles para reventa sin volver a descontar insumos ni generar costo adicional.
              </p>
            </div>

            {preparados.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {preparados.map((p) => (
                  <div key={p.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between shadow-lg">
                    <div>
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/60 text-amber-400 border border-amber-800/60">
                          En espera: {p.minutos_espera} min
                        </span>
                        <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/60">
                          DISPONIBLE
                        </span>
                      </div>
                      <h3 className="font-bold text-sm text-slate-100">{p.producto_nombre}</h3>
                      {p.variacion_snapshot?.modificaciones && (
                        <div className="mt-2 text-xs text-amber-300/80 bg-slate-950 p-2 rounded-lg border border-slate-800">
                          Modificaciones: {p.variacion_snapshot.modificaciones.join(', ')}
                        </div>
                      )}
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-800 flex justify-between items-center">
                      <span className="text-[10px] text-slate-500">Orden origen: #{p.consecutivo_origen || p.pedido_origen_id}</span>
                      <button
                        onClick={() => setDescartandoId(p.id)}
                        className="px-3 py-1 bg-red-950/60 hover:bg-red-900/60 text-red-300 border border-red-800/60 rounded-lg text-xs font-bold transition cursor-pointer"
                      >
                        Descartar (Merma)
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 bg-slate-900/40 rounded-2xl border border-slate-800 text-slate-500 text-xs">
                ✓ No hay platos preparados en espera. Todos los pedidos cancelados fueron gestionados o reutilizados.
              </div>
            )}

            {/* Modal de Confirmación de Descarte */}
            {descartandoId !== null && (
              <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
                <div className="bg-slate-900 border border-red-800 rounded-2xl w-full max-w-sm p-5 shadow-2xl">
                  <h3 className="text-sm font-black text-red-300 uppercase mb-2 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-red-400" />
                    Descartar Alimento Preparado
                  </h3>
                  <p className="text-xs text-slate-400 mb-3">
                    Esta acción marcará el producto como <strong>DESCARTADO</strong> y se computará en el fotograma del cierre de turno como desperdicio/merma.
                  </p>

                  <div className="mb-4">
                    <label className="block text-xs font-bold text-slate-300 mb-1">Motivo del descarte:</label>
                    <input
                      type="text"
                      value={motivoDescarte}
                      onChange={(e) => setMotivoDescarte(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white text-xs focus:outline-none"
                    />
                  </div>

                  <div className="flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setDescartandoId(null)}
                      className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-white cursor-pointer"
                    >
                      Cancelar
                    </button>
                    <button
                      type="button"
                      onClick={() => handleConfirmarDescarte(descartandoId)}
                      className="px-4 py-1.5 rounded-lg text-xs font-bold bg-red-600 hover:bg-red-500 text-white cursor-pointer"
                    >
                      Confirmar Descarte
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ======================================================== */}
        {/* PESTAÑA 5: BITÁCORA DE AUDITORÍA */}
        {/* ======================================================== */}
        {tabActiva === 'AUDITORIA' && (
          <div className="space-y-4 animate-fade-in">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <History className="w-5 h-5 text-purple-400" />
                  Bitácora Inmutable de Operaciones (Auditoría)
                </h2>
                <p className="text-xs text-slate-400">
                  Registro criptográfico de cancelaciones, salidas de caja, compras, aperturas y cierres de turno.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Filtrar acción..."
                  value={filtroAccion}
                  onChange={(e) => setFiltroAccion(e.target.value)}
                  className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none"
                />
                <button
                  onClick={cargarAuditoria}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold transition cursor-pointer"
                >
                  Filtrar
                </button>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 font-bold uppercase">
                  <tr>
                    <th className="p-3">Fecha / Hora</th>
                    <th className="p-3">Usuario</th>
                    <th className="p-3">Acción Registrada</th>
                    <th className="p-3">Entidad</th>
                    <th className="p-3">Detalle Operacional</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {auditoria.length > 0 ? (
                    auditoria.map((aud) => (
                      <tr key={aud.id} className="hover:bg-slate-800/40 transition">
                        <td className="p-3 font-mono text-slate-400 whitespace-nowrap">
                          {new Date(aud.creado_en).toLocaleString('es-CO')}
                        </td>
                        <td className="p-3 font-semibold text-slate-200 flex items-center gap-1.5">
                          <User className="w-3.5 h-3.5 text-slate-400" />
                          <span>{aud.usuario_nombre || `Usuario #${aud.usuario_id}`}</span>
                        </td>
                        <td className="p-3">
                          <span className="font-mono px-2 py-0.5 rounded text-[11px] font-bold bg-purple-950/60 text-purple-300 border border-purple-800/60">
                            {aud.accion}
                          </span>
                        </td>
                        <td className="p-3 font-mono text-slate-400">
                          {aud.entidad ? `${aud.entidad} #${aud.entidad_id || ''}` : '-'}
                        </td>
                        <td className="p-3 text-slate-300 font-mono text-[11px] max-w-xs truncate">
                          {aud.detalle || '-'}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="text-center py-6 text-slate-500 text-xs">
                        No hay registros que coincidan con la búsqueda.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* PESTAÑA 5: RECETAS DEL MENÚ & ESCANDALLO */}
        {/* ======================================================== */}
        {tabActiva === 'RECETAS' && (
          <div className="space-y-4 animate-fade-in">
            {/* Cabecera explicativa */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-lg">
              <div>
                <h2 className="text-base font-black text-white flex items-center gap-2">
                  <UtensilsCrossed className="w-5 h-5 text-purple-400" />
                  <span>Configuración de Recetas y Escandallos</span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Modifica los ingredientes de cada plato. Los ingredientes aquí definidos controlan las opciones de
                  <strong className="text-purple-300"> "Quitar / Modificar" </strong>
                  en la comanda y el descuento automático de stock en cocina.
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => {
                    setNuevoProdCategoriaId(categorias[0]?.id || '')
                    setNuevoProdModalOpen(true)
                  }}
                  className="py-2 px-3.5 bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-bold text-xs rounded-xl shadow-lg shadow-emerald-950/40 flex items-center gap-1.5 transition cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Nuevo Plato / Hamburguesa</span>
                </button>

                <button
                  type="button"
                  onClick={() => setNuevoIngModalOpen(true)}
                  className="py-2 px-3.5 bg-purple-600 hover:bg-purple-500 active:scale-95 text-white font-bold text-xs rounded-xl shadow-lg shadow-purple-950/40 flex items-center gap-1.5 transition cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Crear Insumo / Ingrediente</span>
                </button>
              </div>
            </div>

            {/* Layout Dividido: Catálogo a la izquierda, Editor a la derecha */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              {/* Columna Izquierda: Selector de Productos (5 cols) */}
              <div className="lg:col-span-5 bg-slate-900/80 border border-slate-800 rounded-2xl p-3.5 flex flex-col max-h-[750px] shadow-lg">
                {/* Buscador & Categorías */}
                <div className="space-y-2 mb-3">
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={busquedaReceta}
                      onChange={(e) => setBusquedaReceta(e.target.value)}
                      placeholder="Buscar producto del menú..."
                      className="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
                    />
                  </div>

                  <div className="flex gap-1.5 overflow-x-auto no-scrollbar pb-1">
                    <button
                      type="button"
                      onClick={() => setCategoriaRecetaFiltro(null)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-bold whitespace-nowrap transition cursor-pointer ${
                        categoriaRecetaFiltro === null
                          ? 'bg-purple-600 text-white'
                          : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                      }`}
                    >
                      Todos ({productos.length})
                    </button>
                    {categorias.map((c) => (
                      <button
                        key={c.id}
                        type="button"
                        onClick={() => setCategoriaRecetaFiltro(c.id)}
                        className={`px-2.5 py-1 rounded-lg text-xs font-bold whitespace-nowrap transition cursor-pointer ${
                          categoriaRecetaFiltro === c.id
                            ? 'bg-purple-600 text-white'
                            : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                        }`}
                      >
                        {c.nombre}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Lista de productos */}
                <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
                  {productos
                    .filter((p) => {
                      const matchCat = categoriaRecetaFiltro ? p.categoria_id === categoriaRecetaFiltro : true
                      const matchTxt = p.nombre.toLowerCase().includes(busquedaReceta.toLowerCase())
                      return matchCat && matchTxt
                    })
                    .map((p) => {
                      const isSelected = productoSeleccionado?.id === p.id
                      const esCocina = p.es_cocina !== false
                      const cantIngredientes = p.ingredientes_receta?.length || 0

                      return (
                        <div
                          key={p.id}
                          onClick={() => handleSeleccionarProducto(p)}
                          className={`p-2.5 rounded-xl border transition cursor-pointer flex items-center justify-between gap-2 ${
                            isSelected
                              ? 'bg-purple-950/70 border-purple-500 shadow-md shadow-purple-950/50'
                              : 'bg-slate-950/80 border-slate-800/80 hover:border-slate-700'
                          }`}
                        >
                          <div className="flex-1 min-w-0">
                            <p className="font-bold text-xs text-white truncate">{p.nombre}</p>
                            <div className="flex items-center gap-1.5 mt-0.5">
                              <span className="text-[10px] text-emerald-400 font-mono font-bold">
                                ${Number(p.precio || 0).toLocaleString('es-CO')}
                              </span>
                              {esCocina ? (
                                cantIngredientes > 0 ? (
                                  <span className="text-[10px] bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 px-1.5 rounded">
                                    {cantIngredientes} insumos
                                  </span>
                                ) : (
                                  <span className="text-[10px] bg-amber-950/60 text-amber-400 border border-amber-800/60 px-1.5 rounded">
                                    Sin receta
                                  </span>
                                )
                              ) : (
                                <span className="text-[10px] bg-sky-950/60 text-sky-400 border border-sky-800/60 px-1.5 rounded">
                                  Bebida / No cocina
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="shrink-0">
                            <span
                              className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs ${
                                isSelected ? 'bg-purple-500 text-slate-950' : 'text-slate-500'
                              }`}
                            >
                              →
                            </span>
                          </div>
                        </div>
                      )
                    })}
                </div>
              </div>

              {/* Columna Derecha: Editor de Receta del Producto (7 cols) */}
              <div className="lg:col-span-7 bg-slate-900/90 border border-slate-800 rounded-2xl p-4 flex flex-col shadow-lg">
                {productoSeleccionado ? (
                  <div className="flex flex-col h-full space-y-4">
                    {/* Encabezado del Producto */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400 bg-purple-950/60 border border-purple-800/60 px-2 py-0.5 rounded-md">
                            Editor de Receta
                          </span>
                          {productoSeleccionado.es_cocina !== false ? (
                            <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-2 py-0.5 rounded-md">
                              Producto de Cocina
                            </span>
                          ) : (
                            <span className="text-[10px] font-bold text-sky-400 bg-sky-950/60 border border-sky-800/60 px-2 py-0.5 rounded-md">
                              Bebida / Retail
                            </span>
                          )}
                        </div>
                        <h3 className="text-lg font-black text-white mt-1">
                          {productoSeleccionado.nombre}
                        </h3>
                        <p className="text-xs text-slate-400">
                          {productoSeleccionado.descripcion || 'Sin descripción'}
                        </p>
                      </div>

                      <div className="flex flex-col sm:items-end gap-1.5 shrink-0">
                        <div className="text-right">
                          <span className="text-[10px] text-slate-500 block uppercase font-bold tracking-wider">Precio al Cliente</span>
                          <span className="text-base font-black text-emerald-400 font-mono">
                            ${Number(productoSeleccionado.precio || 0).toLocaleString('es-CO')}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <button
                            type="button"
                            onClick={() => handleAbrirEditarProducto(productoSeleccionado)}
                            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white rounded-lg text-xs font-bold flex items-center gap-1.5 transition cursor-pointer border border-slate-700"
                            title="Modificar precio, nombre o categoría"
                          >
                            <Pencil className="w-3 h-3 text-amber-400" />
                            <span>Editar Precio / Datos</span>
                          </button>
                          <button
                            type="button"
                            onClick={handleDesactivarProducto}
                            disabled={eliminandoProducto}
                            className="p-1.5 bg-rose-950/60 hover:bg-rose-900 border border-rose-800/80 text-rose-300 hover:text-rose-100 rounded-lg text-xs font-bold transition cursor-pointer"
                            title="Desactivar este plato del menú"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Explicación de impacto */}
                    <div className="p-3 bg-purple-950/30 border border-purple-800/40 rounded-xl text-xs text-purple-200">
                      <strong>💡 Impacto en el Restaurante:</strong> Cada ingrediente que agregues aquí se
                      descontará automáticamente del stock al preparar pedidos en cocina, y se mostrará
                      en la comanda como opción de <strong>"Quitar / Modificar" (ej. "Sin tomate", "Sin tocineta")</strong>.
                    </div>

                    {/* Finanzas del Plato en Tiempo Real */}
                    {(() => {
                      const costoReceta = recetaLineas.reduce((acc, l) => {
                        const ing = ingredientes.find((i) => i.id === l.ingrediente_id)
                        const c = ing ? Number(ing.costo_unitario || 0) : 0
                        return acc + (Number(l.cantidad) || 0) * c
                      }, 0)
                      const precio = Number(productoSeleccionado.precio || 0)
                      const utilidad = precio - costoReceta
                      const margen = precio > 0 ? (utilidad / precio) * 100 : 0

                      return (
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-3 bg-slate-950 border border-slate-800 rounded-xl font-mono text-center">
                          <div className="bg-slate-900/90 p-2 rounded-lg border border-slate-800">
                            <span className="text-[10px] text-slate-500 font-sans block">Costo de Insumos</span>
                            <span className="text-xs sm:text-sm font-bold text-amber-400">
                              ${costoReceta.toLocaleString('es-CO')}
                            </span>
                          </div>
                          <div className="bg-slate-900/90 p-2 rounded-lg border border-slate-800">
                            <span className="text-[10px] text-slate-500 font-sans block">Precio Carta</span>
                            <span className="text-xs sm:text-sm font-bold text-white">
                              ${precio.toLocaleString('es-CO')}
                            </span>
                          </div>
                          <div className="bg-slate-900/90 p-2 rounded-lg border border-slate-800">
                            <span className="text-[10px] text-slate-500 font-sans block">Utilidad Bruta</span>
                            <span
                              className={`text-xs sm:text-sm font-bold ${
                                utilidad >= 0 ? 'text-emerald-400' : 'text-rose-400'
                              }`}
                            >
                              ${utilidad.toLocaleString('es-CO')}
                            </span>
                          </div>
                          <div className="bg-slate-900/90 p-2 rounded-lg border border-slate-800">
                            <span className="text-[10px] text-slate-500 font-sans block">Margen</span>
                            <span
                              className={`text-xs sm:text-sm font-bold ${
                                margen >= 50 ? 'text-emerald-400' : 'text-amber-400'
                              }`}
                            >
                              {margen.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      )
                    })()}

                    {recetaError && (
                      <div className="p-2.5 bg-rose-950/80 border border-rose-800 text-rose-300 rounded-xl text-xs">
                        {recetaError}
                      </div>
                    )}

                    {/* Tabla de Ingredientes de la Receta */}
                    <div className="flex-1 overflow-y-auto space-y-2">
                      <div className="flex items-center justify-between">
                        <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                          Ingredientes que componen este producto ({recetaLineas.length}):
                        </label>
                        <button
                          type="button"
                          onClick={handleAgregarLineaReceta}
                          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-purple-300 hover:text-white rounded-lg text-xs font-bold flex items-center gap-1 cursor-pointer transition"
                        >
                          <Plus className="w-3.5 h-3.5" />
                          <span>Añadir Ingrediente</span>
                        </button>
                      </div>

                      {recetaLoading ? (
                        <div className="py-12 flex flex-col items-center justify-center text-slate-500 text-xs">
                          <RefreshCw className="w-6 h-6 animate-spin text-purple-500 mb-2" />
                          <span>Cargando receta...</span>
                        </div>
                      ) : recetaLineas.length === 0 ? (
                        <div className="py-10 text-center border-2 border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
                          Este producto actualmente no tiene receta configurada.
                          <div className="mt-2">
                            <button
                              type="button"
                              onClick={handleAgregarLineaReceta}
                              className="text-purple-400 hover:underline font-bold"
                            >
                              + Haz clic aquí para añadir el primer ingrediente
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {recetaLineas.map((linea, idx) => (
                            <div
                              key={idx}
                              className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl flex items-center gap-2 group hover:border-slate-700 transition"
                            >
                                {/* Selector de Ingrediente */}
                                <div className="flex-1">
                                  <label className="block text-[10px] text-slate-500 mb-0.5">
                                    Ingrediente / Insumo
                                  </label>
                                  <select
                                    value={linea.ingrediente_id}
                                    onChange={(e) =>
                                      handleModificarLineaReceta(idx, 'ingrediente_id', Number(e.target.value))
                                    }
                                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-semibold"
                                  >
                                    {ingredientes.map((ing) => (
                                      <option key={ing.id} value={ing.id}>
                                        {ing.nombre} ({ing.stock_actual} {ing.unidad_base} en stock)
                                      </option>
                                    ))}
                                  </select>
                                </div>

                                {/* Cantidad */}
                                <div className="w-24">
                                  <label className="block text-[10px] text-slate-500 mb-0.5">
                                    Cantidad
                                  </label>
                                  <input
                                    type="number"
                                    step="0.01"
                                    min="0.01"
                                    value={linea.cantidad}
                                    onChange={(e) =>
                                      handleModificarLineaReceta(idx, 'cantidad', parseFloat(e.target.value) || 0)
                                    }
                                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono text-center font-bold"
                                  />
                                </div>

                                {/* Unidad */}
                                <div className="w-24">
                                  <label className="block text-[10px] text-slate-500 mb-0.5">
                                    Unidad
                                  </label>
                                  <input
                                    type="text"
                                    value={linea.unidad}
                                    onChange={(e) =>
                                      handleModificarLineaReceta(idx, 'unidad', e.target.value)
                                    }
                                    placeholder="u, lonja, g..."
                                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none focus:border-purple-500 font-mono text-center"
                                  />
                                </div>

                                {/* Botón Eliminar Fila */}
                                <div className="pt-4">
                                  <button
                                    type="button"
                                    onClick={() => handleEliminarLineaReceta(idx)}
                                    className="p-1.5 rounded-lg bg-rose-950/60 hover:bg-rose-900 text-rose-300 hover:text-white transition cursor-pointer"
                                    title="Quitar este ingrediente de la receta"
                                  >
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              </div>
                            ))}
                        </div>
                      )}
                    </div>

                    {/* Vista Previa de Opciones en Comanda */}
                    {recetaLineas.length > 0 && (
                      <div className="p-3 bg-slate-950/90 border border-slate-800 rounded-xl">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-orange-400 block mb-1.5">
                          Vista previa: Opciones que verá el mesero y la caja para este plato:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {recetaLineas.map((linea, i) => {
                            const ing = ingredientes.find((item) => item.id === linea.ingrediente_id)
                            return (
                              <span
                                key={i}
                                className="text-[10px] bg-orange-950/70 border border-orange-800/70 text-orange-300 px-2 py-0.5 rounded-md font-medium"
                              >
                                Sin {ing?.nombre || `Insumo #${linea.ingrediente_id}`}
                              </span>
                            )
                          })}
                        </div>
                      </div>
                    )}

                    {/* Botón Guardar Receta */}
                    <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                      <button
                        type="button"
                        onClick={handleAgregarLineaReceta}
                        className="py-2.5 px-3.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold rounded-xl text-xs flex items-center gap-1.5 cursor-pointer transition"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Añadir Otro Insumo</span>
                      </button>

                      <button
                        type="button"
                        disabled={guardandoReceta}
                        onClick={handleGuardarReceta}
                        className="py-2.5 px-5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 active:scale-95 text-white font-black text-xs rounded-xl shadow-xl shadow-purple-950/50 flex items-center gap-2 cursor-pointer transition disabled:opacity-50"
                      >
                        {guardandoReceta ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            <span>Guardando Receta...</span>
                          </>
                        ) : (
                          <>
                            <Save className="w-4 h-4" />
                            <span>Guardar Receta del Producto</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="py-20 flex flex-col items-center justify-center text-slate-500 text-xs">
                    <UtensilsCrossed className="w-10 h-10 text-slate-700 mb-2" />
                    <span>Selecciona un producto del catálogo para ver o editar su receta.</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* PESTAÑA: EQUIPO, USUARIOS Y SEGURIDAD */}
        {/* ======================================================== */}
        {tabActiva === 'USUARIOS' && (
          <div className="animate-fade-in">
            <UsuariosTab />
          </div>
        )}

        {/* ======================================================== */}
        {/* PESTAÑA: ASISTENCIA Y TURNOS                             */}
        {/* ======================================================== */}
        {tabActiva === 'ASISTENCIA' && (
          <div className="animate-fade-in">
            <AsistenciaTab />
          </div>
        )}

        {/* ======================================================== */}
        {/* PESTAÑA: CONFIGURACIÓN GLOBAL DEL RESTAURANTE */}
        {/* ======================================================== */}
        {tabActiva === 'CONFIGURACION' && (
          <div className="animate-fade-in">
            <ConfiguracionTab />
          </div>
        )}

        {/* Modal Rápido: Crear Nuevo Ingrediente */}
        {nuevoIngModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 animate-fade-in">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-5 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                <h3 className="text-base font-black text-white flex items-center gap-2">
                  <Plus className="w-4 h-4 text-purple-400" />
                  <span>Nuevo Insumo en el Sistema</span>
                </h3>
                <button
                  type="button"
                  onClick={() => setNuevoIngModalOpen(false)}
                  className="text-slate-400 hover:text-white p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    Nombre del Insumo / Ingrediente *
                  </label>
                  <input
                    type="text"
                    value={nuevoIngNombre}
                    onChange={(e) => setNuevoIngNombre(e.target.value)}
                    placeholder="ej. Tocineta, Pepinillos, Jalapeños..."
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-purple-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1">
                      Unidad Base *
                    </label>
                    <select
                      value={nuevoIngUnidad}
                      onChange={(e) => setNuevoIngUnidad(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-purple-500"
                    >
                      <option value="UNIDAD">UNIDAD</option>
                      <option value="GRAMO">GRAMO</option>
                      <option value="MILILITRO">MILILITRO</option>
                      <option value="LONJA">LONJA</option>
                      <option value="PORCION">PORCION</option>
                      <option value="PAQUETE">PAQUETE</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1">
                      Stock Inicial
                    </label>
                    <input
                      type="number"
                      value={nuevoIngStock}
                      onChange={(e) => setNuevoIngStock(parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    Costo Unitario Estimado ($ COP)
                  </label>
                  <input
                    type="number"
                    value={nuevoIngCosto}
                    onChange={(e) => setNuevoIngCosto(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-purple-500 font-mono"
                  />
                </div>
              </div>

              <div className="pt-4 mt-4 border-t border-slate-800 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setNuevoIngModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-xl text-xs cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  disabled={creandoIngrediente || !nuevoIngNombre.trim()}
                  onClick={handleCrearNuevoIngrediente}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 active:scale-95 text-white font-bold rounded-xl text-xs shadow-lg shadow-purple-950/50 cursor-pointer disabled:opacity-50"
                >
                  {creandoIngrediente ? 'Creando...' : 'Crear Insumo'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Crear Nuevo Producto / Hamburguesa */}
        {nuevoProdModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 animate-fade-in">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-5 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                <h3 className="text-base font-black text-white flex items-center gap-2">
                  <Plus className="w-4 h-4 text-emerald-400" />
                  <span>Crear Nuevo Plato / Producto</span>
                </h3>
                <button
                  type="button"
                  onClick={() => setNuevoProdModalOpen(false)}
                  className="text-slate-400 hover:text-white p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    Nombre del Plato / Hamburguesa *
                  </label>
                  <input
                    type="text"
                    value={nuevoProdNombre}
                    onChange={(e) => setNuevoProdNombre(e.target.value)}
                    placeholder="ej. Hamburguesa Doble Queso Tocino"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-emerald-500 font-bold"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1">
                      Categoría *
                    </label>
                    <select
                      value={nuevoProdCategoriaId}
                      onChange={(e) => setNuevoProdCategoriaId(Number(e.target.value))}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-emerald-500 font-semibold"
                    >
                      {categorias.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.nombre}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1">
                      Precio de Venta ($ COP) *
                    </label>
                    <input
                      type="number"
                      step="500"
                      value={nuevoProdPrecio}
                      onChange={(e) => setNuevoProdPrecio(parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-emerald-400 focus:outline-none focus:border-emerald-500 font-mono font-bold"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    Descripción (opcional)
                  </label>
                  <textarea
                    rows={2}
                    value={nuevoProdDescripcion}
                    onChange={(e) => setNuevoProdDescripcion(e.target.value)}
                    placeholder="ej. Pan brioche, 150g carne angus, queso cheddar y tocineta crocante..."
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-emerald-500 resize-none"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-800 mt-4">
                <button
                  type="button"
                  onClick={() => setNuevoProdModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-bold transition"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  disabled={creandoProducto || !nuevoProdNombre.trim() || !nuevoProdCategoriaId}
                  onClick={handleCrearNuevoProducto}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-bold rounded-xl text-xs shadow-lg shadow-emerald-950/50 cursor-pointer disabled:opacity-50"
                >
                  {creandoProducto ? 'Creando...' : 'Crear Plato'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Editar Plato / Precio / Datos */}
        {editarProdModalOpen && productoSeleccionado && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 animate-fade-in">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-5 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                <h3 className="text-base font-black text-white flex items-center gap-2">
                  <Pencil className="w-4 h-4 text-amber-400" />
                  <span>Modificar Precio y Datos del Plato</span>
                </h3>
                <button
                  type="button"
                  onClick={() => setEditarProdModalOpen(false)}
                  className="text-slate-400 hover:text-white p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    Nombre del Plato *
                  </label>
                  <input
                    type="text"
                    value={editarProdNombre}
                    onChange={(e) => setEditarProdNombre(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-amber-500 font-bold"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1">
                      Precio Carta ($ COP) *
                    </label>
                    <input
                      type="number"
                      step="500"
                      value={editarProdPrecio}
                      onChange={(e) => setEditarProdPrecio(parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-emerald-400 focus:outline-none focus:border-amber-500 font-mono font-bold"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-300 mb-1">
                      Categoría
                    </label>
                    <select
                      value={editarProdCategoriaId}
                      onChange={(e) => setEditarProdCategoriaId(Number(e.target.value))}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-amber-500 font-semibold"
                    >
                      {categorias.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.nombre}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    Descripción
                  </label>
                  <textarea
                    rows={2}
                    value={editarProdDescripcion}
                    onChange={(e) => setEditarProdDescripcion(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-amber-500 resize-none"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-800 mt-4">
                <button
                  type="button"
                  onClick={() => setEditarProdModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-bold transition"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  disabled={guardandoEdicionProd || !editarProdNombre.trim()}
                  onClick={handleGuardarEditarProducto}
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-400 active:scale-95 text-slate-950 font-bold rounded-xl text-xs shadow-lg shadow-amber-950/50 cursor-pointer disabled:opacity-50"
                >
                  {guardandoEdicionProd ? 'Guardando...' : 'Guardar Cambios'}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default Admin
