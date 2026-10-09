import React, { useState, useEffect } from 'react'
import {
  ShieldAlert,
  Clock,
  Store,
  Percent,
  CheckCircle2,
  AlertCircle,
  Save,
  RefreshCw,
  Sliders,
  HelpCircle,
  Trash2,
  X,
  KeyRound,
  FlaskConical,
  Layers,
  Package,
  Users,
  Printer,
} from 'lucide-react'
import {
  getConfiguracionApi,
  setConfiguracionApi,
  getResetResumenApi,
  resetSistemaApi,
} from '../../api/admin'
import type { ResetResumenOut } from '../../types/admin'
import { AdicionesManager } from './AdicionesManager'
import { ConfiguracionImpresoraModal } from '../common/ConfiguracionImpresoraModal'

export const ConfiguracionTab: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [mensaje, setMensaje] = useState<{ tipo: 'ok' | 'error'; texto: string } | null>(null)

  // Asistente de Puesta en Blanco Granular
  const [modalResetOpen, setModalResetOpen] = useState(false)
  const [resumenReset, setResumenReset] = useState<ResetResumenOut | null>(null)
  const [cargandoResumen, setCargandoResumen] = useState(false)
  const [opcionesReset, setOpcionesReset] = useState({
    solo_demo: true,
    transacciones: false,
    inventario: false,
    insumos: false,
    menu: false,
    usuarios: false,
  })
  const [passwordAdminReset, setPasswordAdminReset] = useState('')
  const [ejecutandoReset, setEjecutandoReset] = useState(false)
  const [errorReset, setErrorReset] = useState<string | null>(null)
  const [modalImpresoraOpen, setModalImpresoraOpen] = useState(false)

  // Config variables
  const [politicaStock, setPoliticaStock] = useState<'BLOQUEAR' | 'ADVERTIR_Y_PERMITIR'>('ADVERTIR_Y_PERMITIR')
  const [nombreLocal, setNombreLocal] = useState('Mr. Burger Cali')
  const [minutosCocina, setMinutosCocina] = useState('28')
  const [ivaPorcentaje, setIvaPorcentaje] = useState('0')
  const [modoImpuestos, setModoImpuestos] = useState('INCLUIDO')

  const cargarConfiguracion = async () => {
    try {
      setLoading(true)
      const data = await getConfiguracionApi()
      const mapa = new Map(data.map((c) => [c.clave, c.valor]))

      if (mapa.has('politica_stock_insuficiente')) {
        const val = mapa.get('politica_stock_insuficiente')?.trim().toUpperCase()
        setPoliticaStock(val === 'BLOQUEAR' ? 'BLOQUEAR' : 'ADVERTIR_Y_PERMITIR')
      }
      if (mapa.has('nombre_local')) {
        setNombreLocal(mapa.get('nombre_local') || 'Mr. Burger Cali')
      }
      if (mapa.has('minutos_cocina')) {
        setMinutosCocina(mapa.get('minutos_cocina') || '28')
      }
      if (mapa.has('iva_porcentaje')) {
        setIvaPorcentaje(mapa.get('iva_porcentaje') || '0')
      }
      if (mapa.has('modo_impuestos')) {
        setModoImpuestos(mapa.get('modo_impuestos') || 'INCLUIDO')
      }
    } catch {
      setMensaje({ tipo: 'error', texto: 'Error al consultar configuraciones del restaurante' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    cargarConfiguracion()
  }, [])

  const handleGuardar = async (e: React.FormEvent) => {
    e.preventDefault()
    setGuardando(true)
    setMensaje(null)
    try {
      await Promise.all([
        setConfiguracionApi('politica_stock_insuficiente', politicaStock),
        setConfiguracionApi('nombre_local', nombreLocal.trim()),
        setConfiguracionApi('minutos_cocina', minutosCocina.trim()),
        setConfiguracionApi('iva_porcentaje', ivaPorcentaje.trim()),
        setConfiguracionApi('modo_impuestos', modoImpuestos.trim()),
      ])
      setMensaje({ tipo: 'ok', texto: '✓ ¡Configuraciones guardadas y aplicadas inmediatamente!' })
      setTimeout(() => setMensaje(null), 5000)
    } catch (err: any) {
      setMensaje({
        tipo: 'error',
        texto: err.response?.data?.detail || 'Error al actualizar configuraciones',
      })
    } finally {
      setGuardando(false)
    }
  }

  const handleAbrirModalReset = async () => {
    setErrorReset(null)
    setPasswordAdminReset('')
    setOpcionesReset({
      solo_demo: true,
      transacciones: false,
      inventario: false,
      insumos: false,
      menu: false,
      usuarios: false,
    })
    setModalResetOpen(true)
    try {
      setCargandoResumen(true)
      const data = await getResetResumenApi()
      setResumenReset(data)
    } catch (err: any) {
      console.error('Error al obtener resumen de reset:', err)
    } finally {
      setCargandoResumen(false)
    }
  }

  const handleEjecutarReset = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorReset(null)

    if (!passwordAdminReset.trim()) {
      setErrorReset('Ingresa la contraseña de tu usuario Administrador activo')
      return
    }

    const algunaOpcion = Object.values(opcionesReset).some(Boolean)
    if (!algunaOpcion) {
      setErrorReset('Selecciona al menos una opción para restablecer')
      return
    }

    try {
      setEjecutandoReset(true)
      const res = await resetSistemaApi({
        password_admin: passwordAdminReset,
        ...opcionesReset,
      })
      try {
        localStorage.removeItem('pos_mesero_offline_queue')
      } catch {
        // ignore
      }
      setModalResetOpen(false)
      setPasswordAdminReset('')
      setMensaje({ tipo: 'ok', texto: `✓ ${res.mensaje}` })
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Error al restablecer el sistema. Verifica tu contraseña.'
      setErrorReset(msg)
    } finally {
      setEjecutandoReset(false)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-400 gap-3">
        <RefreshCw className="w-8 h-8 animate-spin text-purple-500" />
        <p className="text-sm">Cargando parámetros del restaurante...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Banner de Feedback */}
      {mensaje && (
        <div
          className={`flex items-center gap-3 p-4 rounded-xl text-sm font-semibold border transition-all ${
            mensaje.tipo === 'ok'
              ? 'bg-emerald-950/80 border-emerald-600/60 text-emerald-300'
              : 'bg-rose-950/80 border-rose-600/60 text-rose-300'
          }`}
        >
          {mensaje.tipo === 'ok' ? (
            <CheckCircle2 className="w-5 h-5 shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 shrink-0" />
          )}
          <span>{mensaje.texto}</span>
        </div>
      )}

      <form onSubmit={handleGuardar} className="space-y-6">
        {/* SECCIÓN 1: POLÍTICA ANTE FALTA DE STOCK */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Política de Inventario ante Stock Agotado
              </h2>
              <p className="text-xs text-slate-400">
                Determina qué ocurre cuando un mesero o cajero intenta vender un producto cuyos insumos
                (carne, pan, salsas) han llegado a 0 en el sistema.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {/* OPCION BLOQUEAR */}
            <label
              className={`relative flex flex-col p-4 rounded-xl border-2 cursor-pointer transition-all ${
                politicaStock === 'BLOQUEAR'
                  ? 'bg-purple-950/40 border-purple-500 text-white shadow-lg shadow-purple-950/40'
                  : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-black text-sm uppercase tracking-wide flex items-center gap-2 text-rose-400">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
                  BLOQUEAR (Estricto)
                </span>
                <input
                  type="radio"
                  name="politicaStock"
                  value="BLOQUEAR"
                  checked={politicaStock === 'BLOQUEAR'}
                  onChange={() => setPoliticaStock('BLOQUEAR')}
                  className="w-4 h-4 text-purple-600 bg-slate-900 border-slate-700 focus:ring-purple-500"
                />
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Si falta algún ingrediente, el sistema <strong>rechaza la comanda</strong> e informa
                al personal qué insumo está agotado. Garantiza que jamás se venda lo que no hay en bodega.
              </p>
              <div className="mt-3 text-[11px] font-medium text-slate-500 bg-slate-900/60 p-2 rounded-lg border border-slate-800">
                Recomendado para locales con control estricto de bodega en tiempo real.
              </div>
            </label>

            {/* OPCION ADVERTIR Y PERMITIR */}
            <label
              className={`relative flex flex-col p-4 rounded-xl border-2 cursor-pointer transition-all ${
                politicaStock === 'ADVERTIR_Y_PERMITIR'
                  ? 'bg-purple-950/40 border-purple-500 text-white shadow-lg shadow-purple-950/40'
                  : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-black text-sm uppercase tracking-wide flex items-center gap-2 text-amber-400">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                  ADVERTIR Y PERMITIR (Flexible)
                </span>
                <input
                  type="radio"
                  name="politicaStock"
                  value="ADVERTIR_Y_PERMITIR"
                  checked={politicaStock === 'ADVERTIR_Y_PERMITIR'}
                  onChange={() => setPoliticaStock('ADVERTIR_Y_PERMITIR')}
                  className="w-4 h-4 text-purple-600 bg-slate-900 border-slate-700 focus:ring-purple-500"
                />
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Permite enviar la comanda normalmente y registra el consumo <strong>llevando el saldo
                a números negativos</strong> temporalmente.
              </p>
              <div className="mt-3 text-[11px] font-medium text-slate-500 bg-slate-900/60 p-2 rounded-lg border border-slate-800">
                Ideal si compras insumos de urgencia y continúas vendiendo antes de cargar la factura de compra.
              </div>
            </label>
          </div>
        </div>

        {/* SECCIÓN 2: PARÁMETROS OPERATIVOS */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <div className="w-10 h-10 rounded-xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-400 shrink-0">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Datos del Local e Impuestos
              </h2>
              <p className="text-xs text-slate-400">
                Información impresa en tickets, temporizador del KDS de cocina y régimen tributario.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Nombre del Local */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Store className="w-3.5 h-3.5 text-purple-400" />
                Nombre del Restaurante (Encabezado de Recibo)
              </label>
              <input
                type="text"
                required
                value={nombreLocal}
                onChange={(e) => setNombreLocal(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 transition"
                placeholder="Ej: Mr. Burger Cali"
              />
            </div>

            {/* Temporizador Cocina */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-amber-400" />
                Temporizador Estándar Cocina KDS (Minutos)
              </label>
              <input
                type="number"
                min="5"
                max="120"
                required
                value={minutosCocina}
                onChange={(e) => setMinutosCocina(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 transition"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Al sobrepasar este tiempo, el ticket en cocina cambia a rojo parpadeante.
              </p>
            </div>

            {/* Porcentaje IVA / Impuesto */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Percent className="w-3.5 h-3.5 text-blue-400" />
                  Tarifa de Impuesto / IVA (%)
                </label>
                {Number(ivaPorcentaje) === 0 ? (
                  <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    EXENTO (0%)
                  </span>
                ) : (
                  <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">
                    GRAVADO ({ivaPorcentaje}%)
                  </span>
                )}
              </div>
              <input
                type="number"
                min="0"
                max="100"
                required
                value={ivaPorcentaje}
                onChange={(e) => setIvaPorcentaje(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 transition"
              />
              <div className="text-[11px] text-slate-400 mt-2 space-y-1">
                {Number(ivaPorcentaje) === 0 ? (
                  <p className="text-emerald-400 font-medium">
                    ✓ <strong>Estado Activo:</strong> Todo el sistema (tirillas, comandas, caja y reportes) opera como <strong>Exento de IVA</strong> bajo el Régimen No Responsable (Art. 512-13 E.T.). No se desglosa ni se cobra impuesto al cliente.
                  </p>
                ) : (
                  <p className="text-amber-400 font-medium">
                    ⚠ <strong>Estado Activo:</strong> El sistema calculará y desglosará automáticamente la tarifa del <strong>{ivaPorcentaje}%</strong> en todas las tirillas y comandas.
                  </p>
                )}
                <p className="text-[10px] text-slate-500">
                  Guía: <strong>0%:</strong> Exento / No Responsable | <strong>8%:</strong> Impuesto Nacional al Consumo (INC) | <strong>19%:</strong> IVA General.
                </p>
              </div>
            </div>

            {/* Modo Impuestos */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
                Régimen de Precios
              </label>
              <select
                value={modoImpuestos}
                onChange={(e) => setModoImpuestos(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-purple-500 transition cursor-pointer"
              >
                <option value="INCLUIDO">INCLUIDO (El precio en carta ya contiene los impuestos)</option>
                <option value="MAS_IVA">MÁS IVA (Los impuestos se suman al subtotal en la factura)</option>
              </select>
            </div>
          </div>
        </div>

        {/* SECCIÓN 3: CATÁLOGO DE ADICIONES EXTRA CON COSTO */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <div className="w-10 h-10 rounded-xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-400 shrink-0">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Catálogo de Adiciones Extra con Costo (Opciones en Comanda)
              </h2>
              <p className="text-xs text-slate-400">
                Establece qué adiciones aparecen para los meseros al personalizar platos, cuáles se ocultan, precios y nuevos adicionales.
              </p>
            </div>
          </div>

          <AdicionesManager />
        </div>

        {/* ZONA DE MANTENIMIENTO: ASISTENTE DE PUESTA EN BLANCO */}
        <div className="bg-rose-950/20 border border-rose-800/40 rounded-2xl p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 shrink-0">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  Asistente de Puesta en Blanco y Limpieza de Datos
                  <span className="px-2 py-0.5 rounded-full text-[10px] bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30">
                    Granular y Seguro
                  </span>
                </h3>
                <p className="text-xs text-rose-300/80 mt-0.5">
                  Limpia únicamente pruebas (demo) o restablece selectivamente transacciones, stock o usuarios no protegidos. Requiere la clave del administrador activo.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={handleAbrirModalReset}
              className="px-4 py-2.5 bg-rose-600/30 hover:bg-rose-600 text-rose-200 hover:text-white border border-rose-500/40 rounded-xl text-xs font-bold transition cursor-pointer self-start md:self-auto shrink-0 flex items-center gap-2 shadow-lg shadow-rose-950/40"
            >
              <Trash2 className="w-4 h-4" />
              <span>Abrir Asistente de Puesta en Blanco</span>
            </button>
          </div>
        </div>

        {/* SECCIÓN: IMPRESORA TÉRMICA & GAVETA */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-sky-500/20 border border-sky-500/40 flex items-center justify-center text-sky-400 shrink-0">
                <Printer className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  Impresora Térmica & Gaveta de Dinero RJ11
                </h2>
                <p className="text-xs text-slate-400">
                  Formato de papel (58mm / 80mm), tirillas automáticas y apertura de caja registradora.
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setModalImpresoraOpen(true)}
              className="px-4 py-2.5 bg-sky-600/30 hover:bg-sky-600 text-sky-200 hover:text-white border border-sky-500/40 rounded-xl text-xs font-bold transition cursor-pointer self-start md:self-auto shrink-0 flex items-center gap-2 shadow-lg"
            >
              <Printer className="w-4 h-4" />
              <span>Configurar Impresora & Gaveta</span>
            </button>
          </div>
        </div>

        {/* BOTÓN GUARDAR */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={guardando}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-sm shadow-lg shadow-purple-950/50 transition cursor-pointer disabled:opacity-50"
          >
            {guardando ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Guardando cambios...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>Guardar Configuración</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Modal: Configuración de Impresora */}
      <ConfiguracionImpresoraModal
        isOpen={modalImpresoraOpen}
        onClose={() => setModalImpresoraOpen(false)}
      />

      {/* Modal: Asistente de Puesta en Blanco Granular */}
      {modalResetOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/85 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl max-h-[92vh] overflow-y-auto">
            {/* Cabecera Modal */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-rose-500/20 text-rose-400 border border-rose-500/30">
                  <Trash2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Asistente de Puesta en Blanco</h3>
                  <p className="text-xs text-slate-400">Selecciona qué módulos deseas limpiar o restablecer</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setModalResetOpen(false)}
                className="text-slate-400 hover:text-white transition p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {errorReset && (
              <div className="p-3 mb-4 rounded-xl bg-rose-950/80 border border-rose-800 text-rose-300 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{errorReset}</span>
              </div>
            )}

            {/* Resumen en vivo */}
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3 mb-4 text-xs">
              <div className="font-bold text-slate-300 mb-1.5 flex items-center justify-between">
                <span>Estado actual en la base de datos:</span>
                {cargandoResumen && <RefreshCw className="w-3.5 h-3.5 animate-spin text-purple-400" />}
              </div>
              {resumenReset ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px] text-slate-400">
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block">Pedidos Demo / Totales:</span>
                    <strong className="text-amber-400">{resumenReset.pedidos_demo}</strong> / <strong className="text-white">{resumenReset.pedidos_total}</strong>
                  </div>
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block">Movs. Caja Demo:</span>
                    <strong className="text-amber-400">{resumenReset.movimientos_caja_demo}</strong>
                  </div>
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block">Cuentas Protegidas:</span>
                    <strong className="text-sky-400">{resumenReset.usuarios_fijados}</strong>
                  </div>
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block">Insumos en Bodega:</span>
                    <strong className="text-white">{resumenReset.ingredientes}</strong>
                  </div>
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block">Productos Menú:</span>
                    <strong className="text-white">{resumenReset.productos}</strong>
                  </div>
                  <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                    <span className="text-slate-500 block">Usuarios Borrables:</span>
                    <strong className="text-rose-400">{resumenReset.usuarios_borrables}</strong>
                  </div>
                </div>
              ) : (
                <p className="text-slate-500 italic">Cargando conteos de registros...</p>
              )}
            </div>

            <form onSubmit={handleEjecutarReset} className="space-y-4">
              <div className="space-y-2.5">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
                  Módulos a restablecer:
                </span>

                {/* Opción 1: solo_demo */}
                <label className={`flex items-start gap-3 p-3 rounded-xl border transition cursor-pointer ${
                  opcionesReset.solo_demo
                    ? 'bg-amber-950/40 border-amber-500/60 text-white'
                    : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}>
                  <input
                    type="checkbox"
                    checked={opcionesReset.solo_demo}
                    onChange={(e) => setOpcionesReset({ ...opcionesReset, solo_demo: e.target.checked })}
                    className="mt-1 rounded border-slate-700 text-amber-500 focus:ring-0 bg-slate-900"
                  />
                  <div className="text-xs flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold flex items-center gap-1.5 text-amber-300">
                        <FlaskConical className="w-3.5 h-3.5" /> Solo Operaciones de Prueba / Demo (Recomendado)
                      </span>
                      <span className="text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.2 rounded font-mono font-bold">
                        {resumenReset ? `${resumenReset.pedidos_demo} pedidos` : ''}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5 leading-tight">
                      Elimina única y exclusivamente los pedidos, cobros, vales y turnos de los roles demo (caja, mesero, cocina). Conserva ventas reales y configuraciones.
                    </p>
                  </div>
                </label>

                {/* Opción 2: transacciones */}
                <label className={`flex items-start gap-3 p-3 rounded-xl border transition cursor-pointer ${
                  opcionesReset.transacciones
                    ? 'bg-rose-950/40 border-rose-500/60 text-white'
                    : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}>
                  <input
                    type="checkbox"
                    checked={opcionesReset.transacciones}
                    onChange={(e) => setOpcionesReset({ ...opcionesReset, transacciones: e.target.checked })}
                    className="mt-1 rounded border-slate-700 text-rose-500 focus:ring-0 bg-slate-900"
                  />
                  <div className="text-xs flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold flex items-center gap-1.5 text-rose-300">
                        <Layers className="w-3.5 h-3.5" /> Todas las Transacciones (Ventas, pedidos, cierres y vales)
                      </span>
                      <span className="text-[10px] bg-rose-500/20 text-rose-300 px-1.5 py-0.2 rounded font-mono font-bold">
                        {resumenReset ? `${resumenReset.pedidos_total} pedidos` : ''}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5 leading-tight">
                      Limpia TODO el historial de ventas y turnos de caja (demo y reales). Libera todas las mesas a DISPONIBLE. Conserva catálogo de platos e inventario.
                    </p>
                  </div>
                </label>

                {/* Opción 3: inventario */}
                <label className={`flex items-start gap-3 p-3 rounded-xl border transition cursor-pointer ${
                  opcionesReset.inventario
                    ? 'bg-purple-950/40 border-purple-500/60 text-white'
                    : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}>
                  <input
                    type="checkbox"
                    checked={opcionesReset.inventario}
                    onChange={(e) => setOpcionesReset({ ...opcionesReset, inventario: e.target.checked })}
                    className="mt-1 rounded border-slate-700 text-purple-500 focus:ring-0 bg-slate-900"
                  />
                  <div className="text-xs flex-1">
                    <span className="font-bold flex items-center gap-1.5 text-purple-300">
                      <Package className="w-3.5 h-3.5" /> Inventario y Stock a Cero
                    </span>
                    <p className="text-[11px] text-slate-400 mt-0.5 leading-tight">
                      Pone el stock actual de todos los ingredientes en 0, borra movimientos de kardex y compras registradas.
                    </p>
                  </div>
                </label>

                {/* Opción 4: insumos */}
                <label className={`flex items-start gap-3 p-3 rounded-xl border transition cursor-pointer ${
                  opcionesReset.insumos
                    ? 'bg-blue-950/40 border-blue-500/60 text-white'
                    : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}>
                  <input
                    type="checkbox"
                    checked={opcionesReset.insumos}
                    onChange={(e) => setOpcionesReset({ ...opcionesReset, insumos: e.target.checked })}
                    className="mt-1 rounded border-slate-700 text-blue-500 focus:ring-0 bg-slate-900"
                  />
                  <div className="text-xs flex-1">
                    <span className="font-bold flex items-center gap-1.5 text-blue-300">
                      Catálogo de Insumos y Recetas
                    </span>
                    <p className="text-[11px] text-slate-400 mt-0.5 leading-tight">
                      Elimina el catálogo de ingredientes y las recetas asignadas a los platos (incluye inventario a cero).
                    </p>
                  </div>
                </label>

                {/* Opción 5: menu */}
                <label className={`flex items-start gap-3 p-3 rounded-xl border transition cursor-pointer ${
                  opcionesReset.menu
                    ? 'bg-orange-950/40 border-orange-500/60 text-white'
                    : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}>
                  <input
                    type="checkbox"
                    checked={opcionesReset.menu}
                    onChange={(e) => setOpcionesReset({ ...opcionesReset, menu: e.target.checked })}
                    className="mt-1 rounded border-slate-700 text-orange-500 focus:ring-0 bg-slate-900"
                  />
                  <div className="text-xs flex-1">
                    <span className="font-bold flex items-center gap-1.5 text-orange-300">
                      <Store className="w-3.5 h-3.5" /> Menú de Platos y Categorías (Avanzado)
                    </span>
                    <p className="text-[11px] text-slate-400 mt-0.5 leading-tight">
                      Elimina todos los productos de venta, categorías y combos (exige limpiar transacciones).
                    </p>
                  </div>
                </label>

                {/* Opción 6: usuarios */}
                <label className={`flex items-start gap-3 p-3 rounded-xl border transition cursor-pointer ${
                  opcionesReset.usuarios
                    ? 'bg-indigo-950/40 border-indigo-500/60 text-white'
                    : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}>
                  <input
                    type="checkbox"
                    checked={opcionesReset.usuarios}
                    onChange={(e) => setOpcionesReset({ ...opcionesReset, usuarios: e.target.checked })}
                    className="mt-1 rounded border-slate-700 text-indigo-500 focus:ring-0 bg-slate-900"
                  />
                  <div className="text-xs flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold flex items-center gap-1.5 text-indigo-300">
                        <Users className="w-3.5 h-3.5" /> Usuarios NO Protegidos
                      </span>
                      <span className="text-[10px] bg-sky-500/20 text-sky-300 px-1.5 py-0.2 rounded font-bold">
                        Conserva fijados
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5 leading-tight">
                      Elimina empleados creados no protegidos. Las cuentas marcadas con 📌 Protegida y tu usuario actual NUNCA serán eliminados.
                    </p>
                  </div>
                </label>
              </div>

              {/* Confirmación con Contraseña del Administrador Activo */}
              <div className="pt-3 border-t border-slate-800 space-y-1.5">
                <label className="block text-xs font-bold text-white flex items-center gap-1.5">
                  <KeyRound className="w-4 h-4 text-amber-400" />
                  Contraseña de Administrador Activo (Obligatoria por seguridad)
                </label>
                <input
                  type="password"
                  required
                  placeholder="Digita tu contraseña de admin para autorizar"
                  value={passwordAdminReset}
                  onChange={(e) => setPasswordAdminReset(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 focus:border-rose-500 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none"
                />
                <p className="text-[11px] text-slate-400">
                  Por seguridad, esta operación exige revalidar las credenciales del administrador con la sesión activa.
                </p>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setModalResetOpen(false)}
                  className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl transition cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={ejecutandoReset}
                  className="px-5 py-2.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-xl transition shadow-lg shadow-rose-950/50 flex items-center gap-2 disabled:opacity-50 cursor-pointer"
                >
                  {ejecutandoReset ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Restableciendo...</span>
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-4 h-4" />
                      <span>Confirmar Restablecimiento</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
