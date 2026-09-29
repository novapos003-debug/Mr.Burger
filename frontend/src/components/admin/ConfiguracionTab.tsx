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
} from 'lucide-react'
import { getConfiguracionApi, setConfiguracionApi, limpiarDatosPruebaApi } from '../../api/admin'

export const ConfiguracionTab: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [limpiando, setLimpiando] = useState(false)
  const [confirmarLimpieza, setConfirmarLimpieza] = useState(false)
  const [mensaje, setMensaje] = useState<{ tipo: 'ok' | 'error'; texto: string } | null>(null)

  // Config variables
  const [politicaStock, setPoliticaStock] = useState<'BLOQUEAR' | 'ADVERTIR_Y_PERMITIR'>('BLOQUEAR')
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
        setPoliticaStock(val === 'ADVERTIR_Y_PERMITIR' ? 'ADVERTIR_Y_PERMITIR' : 'BLOQUEAR')
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

  const handleLimpiarPruebas = async () => {
    try {
      setLimpiando(true)
      const res = await limpiarDatosPruebaApi()
      try {
        localStorage.removeItem('pos_mesero_offline_queue')
      } catch {
        // ignore
      }
      setMensaje({ tipo: 'ok', texto: `✓ ${res.mensaje}` })
      setConfirmarLimpieza(false)
    } catch (err: any) {
      setMensaje({
        tipo: 'error',
        texto: err.response?.data?.detail || 'Error al restablecer datos de prueba',
      })
    } finally {
      setLimpiando(false)
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
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Percent className="w-3.5 h-3.5 text-blue-400" />
                Tarifa de Impuesto / IVA (%)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                required
                value={ivaPorcentaje}
                onChange={(e) => setIvaPorcentaje(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 transition"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                <strong>0%:</strong> Régimen No Responsable (Art. 512-13 E.T. - Comida rápida local).<br />
                <strong>8%:</strong> Impoconsumo (Régimen ordinario). <strong>19%:</strong> Franquicias.
              </p>
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

        {/* ZONA DE MANTENIMIENTO: RESTABLECER A CERO PARA PRODUCCIÓN */}
        <div className="bg-rose-950/20 border border-rose-800/40 rounded-2xl p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 shrink-0">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Puesta en Blanco para Producción</h3>
                <p className="text-xs text-rose-300/80">
                  Borra todos los pedidos de prueba, turnos viejos de caja y tickets de cocina. Libera las mesas y restablece el stock. Conserva productos, recetas y usuarios.
                </p>
              </div>
            </div>
            {!confirmarLimpieza ? (
              <button
                type="button"
                onClick={() => setConfirmarLimpieza(true)}
                className="px-4 py-2 bg-rose-600/20 hover:bg-rose-600/40 text-rose-300 border border-rose-500/30 rounded-xl text-xs font-bold transition cursor-pointer self-start md:self-auto shrink-0"
              >
                Restablecer a Cero
              </button>
            ) : (
              <div className="flex items-center gap-2 self-start md:self-auto shrink-0">
                <button
                  type="button"
                  onClick={() => setConfirmarLimpieza(false)}
                  className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  disabled={limpiando}
                  onClick={handleLimpiarPruebas}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-rose-950/50 transition cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                >
                  {limpiando ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                  <span>Confirmar: Borrar Pruebas</span>
                </button>
              </div>
            )}
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
    </div>
  )
}
