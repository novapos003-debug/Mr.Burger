import React, { useState, useEffect } from 'react'
import type { Pedido } from '../../types/mesero'
import type { MetodoPago, CobroIn, CobroOut, PagoIn } from '../../types/caja'
import { cobrarPedido, cambiarTipoConsumoApi } from '../../api/caja'
import {
  X,
  DollarSign,
  CreditCard,
  QrCode,
  FileText,
  Layers,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ShoppingBag,
} from 'lucide-react'

interface Props {
  isOpen: boolean
  pedido: Pedido | null
  ivaPorcentaje?: number
  onClose: () => void
  onSuccess: (resultado: CobroOut) => void
  onPedidoActualizado?: (pedido: Pedido) => void
}

export const CobroModal: React.FC<Props> = ({
  isOpen,
  pedido,
  ivaPorcentaje = 0,
  onClose,
  onSuccess,
  onPedidoActualizado,
}) => {
  const [metodo, setMetodo] = useState<MetodoPago | 'MIXTO'>('EFECTIVO')
  const [recibidoEfectivo, setRecibidoEfectivo] = useState<number>(0)
  const [refTarjeta, setRefTarjeta] = useState<string>('')
  const [refTransferencia, setRefTransferencia] = useState<string>('')
  
  // Datos de Vale (pagaré)
  const [valeNombre, setValeNombre] = useState<string>('')
  const [valeCedula, setValeCedula] = useState<string>('')
  const [valeTelefono, setValeTelefono] = useState<string>('')

  // Pago Mixto
  const [lineasMixtas, setLineasMixtas] = useState<Array<{ metodo: MetodoPago; monto: number; recibido?: number }>>([
    { metodo: 'EFECTIVO', monto: 0, recibido: 0 },
    { metodo: 'TARJETA', monto: 0 },
  ])

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pedidoActual, setPedidoActual] = useState<Pedido | null>(pedido)
  const [cambiandoTipo, setCambiandoTipo] = useState(false)

  const total = Number(pedidoActual?.total || 0)
  const yaPagado = Boolean(
    pedidoActual && (pedidoActual.pagado_en !== null || pedidoActual.estado === 'PAGADO' || pedidoActual.estado === 'CERRADO')
  )

  useEffect(() => {
    if (pedido) {
      setPedidoActual(pedido)
      const t = Number(pedido.total || 0)
      setRecibidoEfectivo(t)
      if (pedido.canal === 'DIDI') {
        setMetodo('DIDI_TARJETA')
      } else {
        setMetodo('EFECTIVO')
      }
      setRefTarjeta('')
      setRefTransferencia('')
      setValeNombre('')
      setValeCedula('')
      setValeTelefono('')
      setError(null)

      // Configurar líneas mixtas por defecto
      const mitad = Math.floor(t / 2)
      setLineasMixtas([
        { metodo: 'EFECTIVO', monto: mitad, recibido: mitad },
        { metodo: 'TARJETA', monto: t - mitad },
      ])
    }
  }, [pedido])

  const handleCambiarTipoConsumo = async (nuevoTipo: 'LOCAL' | 'LLEVAR') => {
    if (!pedidoActual || yaPagado || pedidoActual.tipo_consumo === nuevoTipo) return
    try {
      setCambiandoTipo(true)
      const actualizado = await cambiarTipoConsumoApi(pedidoActual.id, nuevoTipo)
      setPedidoActual(actualizado)
      const nuevoTotal = Number(actualizado.total || 0)
      setRecibidoEfectivo(nuevoTotal)
      const mitad = Math.floor(nuevoTotal / 2)
      setLineasMixtas([
        { metodo: 'EFECTIVO', monto: mitad, recibido: mitad },
        { metodo: 'TARJETA', monto: nuevoTotal - mitad },
      ])
      if (onPedidoActualizado) {
        onPedidoActualizado(actualizado)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cambiar tipo de consumo')
    } finally {
      setCambiandoTipo(false)
    }
  }

  if (!isOpen || !pedidoActual) return null

  // Cálculo del cambio en efectivo
  const cambioEfectivo = Math.max(0, recibidoEfectivo - total)
  const faltaEfectivo = recibidoEfectivo < total ? total - recibidoEfectivo : 0

  // Total acumulado en pago mixto
  const totalMixtoAsignado = lineasMixtas.reduce((acc, l) => acc + Number(l.monto || 0), 0)
  const diferenciaMixto = total - totalMixtoAsignado

  const handleCobrar = async () => {
    try {
      setLoading(true)
      setError(null)

      let payload: CobroIn

      if (metodo === 'MIXTO') {
        if (diferenciaMixto !== 0) {
          setError(`La suma de los pagos debe ser exactamente igual al total ($${total.toLocaleString()} COP). Diferencia: $${Math.abs(diferenciaMixto).toLocaleString()} COP`)
          setLoading(false)
          return
        }

        const pagos: PagoIn[] = lineasMixtas.map((l) => ({
          metodo: l.metodo,
          monto: Number(l.monto),
          recibido: l.metodo === 'EFECTIVO' ? Number(l.recibido || l.monto) : null,
          didi_orden_id: pedidoActual.didi_orden_id,
        }))

        payload = { pagos }
      } else if (metodo === 'EFECTIVO') {
        if (recibidoEfectivo < total) {
          setError(`El monto recibido ($${recibidoEfectivo.toLocaleString()}) es inferior al total a pagar ($${total.toLocaleString()})`)
          setLoading(false)
          return
        }

        payload = {
          pagos: [
            {
              metodo: 'EFECTIVO',
              monto: total,
              recibido: recibidoEfectivo,
            },
          ],
        }
      } else if (metodo === 'TARJETA') {
        payload = {
          pagos: [
            {
              metodo: 'TARJETA',
              monto: total,
              recibido: null,
            },
          ],
        }
      } else if (metodo === 'TRANSFERENCIA') {
        payload = {
          pagos: [
            {
              metodo: 'TRANSFERENCIA',
              monto: total,
              recibido: null,
            },
          ],
        }
      } else if (metodo === 'DIDI_TARJETA' || metodo === 'DIDI_EFECTIVO') {
        payload = {
          pagos: [
            {
              metodo,
              monto: total,
              didi_orden_id: pedidoActual.didi_orden_id || `DIDI-${pedidoActual.consecutivo}`,
              recibido: metodo === 'DIDI_EFECTIVO' ? total : null,
            },
          ],
        }
      } else if (metodo === 'VALE') {
        if (!valeNombre.trim()) {
          setError('El nombre del cliente o responsable del pagaré es obligatorio')
          setLoading(false)
          return
        }

        payload = {
          pagos: [
            {
              metodo: 'VALE',
              monto: total,
              vale_cliente_nombre: valeNombre.trim(),
              vale_cliente_cedula: valeCedula.trim() || null,
              vale_cliente_telefono: valeTelefono.trim() || null,
            },
          ],
        }
      } else {
        throw new Error('Método de pago no reconocido')
      }

      const resultado = await cobrarPedido(pedidoActual.id, payload)
      
      // Abrir cajón monedero si hubo pago en efectivo
      const tieneEfectivo = payload.pagos.some(p => p.metodo === 'EFECTIVO' || p.metodo === 'DIDI_EFECTIVO')
      if (tieneEfectivo) {
        import('../../utils/printer').then(printer => {
          printer.abrirCajonMonedero().catch(e => console.error(e))
        })
      }

      onSuccess(resultado)
      onClose()
    } catch (err: any) {
      console.error('Error al cobrar pedido:', err)
      setError(err.response?.data?.detail || err.message || 'Error al procesar el cobro')
    } finally {
      setLoading(false)
    }
  }

  // Denominaciones rápidas de billetes
  const botonesEfectivo = [
    { label: 'Exacto', val: total },
    { label: '$20k', val: 20000 },
    { label: '$50k', val: 50000 },
    { label: '$100k', val: 100000 },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-3 sm:p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Cabecera del Cobro */}
        <div className="p-4 border-b border-slate-800 bg-slate-800/50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600/30 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <DollarSign className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-black text-white text-lg tracking-wide">
                  {yaPagado ? `Detalle de Pedido #${pedidoActual.consecutivo}` : `Cobrar Pedido #${pedidoActual.consecutivo}`}
                </h2>
                <span className="px-2 py-0.5 rounded text-xs font-bold bg-slate-800 text-slate-300 border border-slate-700">
                  {pedidoActual.canal === 'MESA' ? `Mesa ${pedidoActual.mesa_numero}` : pedidoActual.canal}
                </span>
                {pedidoActual.tipo_consumo === 'LLEVAR' && (
                  <span className="px-2 py-0.5 rounded text-xs font-bold bg-orange-950 text-orange-300 border border-orange-800">
                    🥡 Para Llevar
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400">
                {yaPagado ? 'Este pedido ya fue pagado y procesado' : 'Selecciona el medio de pago y registra la transacción'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Cuerpo */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1">
          {error && (
            <div className="p-3 bg-rose-950/80 border border-rose-800 text-rose-300 rounded-xl text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {/* Selector interactivo de Consumo (Comer Aquí / Para Llevar) */}
          {!yaPagado && (
            <div className="bg-slate-950/80 p-2 rounded-2xl border border-slate-800 flex items-center justify-between gap-2">
              <span className="text-xs font-bold text-slate-300 ml-2 flex items-center gap-2">
                <span>Destino del pedido:</span>
                {cambiandoTipo && <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />}
              </span>
              <div className="flex gap-1.5">
                <button
                  type="button"
                  disabled={cambiandoTipo}
                  onClick={() => handleCambiarTipoConsumo('LOCAL')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer flex items-center gap-1.5 ${
                    (pedidoActual.tipo_consumo || 'LOCAL') === 'LOCAL'
                      ? 'bg-sky-600 text-white shadow-md'
                      : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
                  }`}
                >
                  <span>🍽️ Comer Aquí</span>
                </button>
                <button
                  type="button"
                  disabled={cambiandoTipo}
                  onClick={() => handleCambiarTipoConsumo('LLEVAR')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer flex items-center gap-1.5 ${
                    pedidoActual.tipo_consumo === 'LLEVAR'
                      ? 'bg-orange-600 text-white shadow-md'
                      : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
                  }`}
                >
                  <span>🥡 Para Llevar</span>
                </button>
              </div>
            </div>
          )}

          {/* Desglose Financiero */}
          <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">
                Total a Cobrar
              </span>
              <div className="text-3xl font-black text-emerald-400 font-mono tracking-tight">
                ${total.toLocaleString('es-CO')} <span className="text-sm font-sans text-emerald-500 font-semibold">COP</span>
              </div>
            </div>

            <div className="text-xs text-slate-400 space-y-1 sm:text-right border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-800">
              {pedidoActual.subtotal && (
                <div>Subtotal base: <strong className="text-slate-200 font-mono">${Number(pedidoActual.subtotal).toLocaleString('es-CO')}</strong></div>
              )}
              {pedidoActual.recargo_empaque && Number(pedidoActual.recargo_empaque) > 0 ? (
                <div className="text-orange-400 font-semibold">
                  🥡 Recargo empaque llevar: <strong className="font-mono text-amber-300">+${Number(pedidoActual.recargo_empaque).toLocaleString('es-CO')}</strong>
                </div>
              ) : null}
              {pedidoActual.iva && Number(pedidoActual.iva) > 0 ? (
                <div>
                  IVA ({ivaPorcentaje && ivaPorcentaje > 0 ? ivaPorcentaje : 19}% inc.):{' '}
                  <strong className="text-slate-200 font-mono">${Number(pedidoActual.iva).toLocaleString('es-CO')}</strong>
                </div>
              ) : (
                <div>
                  IVA: <strong className="text-emerald-400 font-semibold">Exento (0%)</strong>
                </div>
              )}
              <div>Productos: <strong className="text-slate-200">{pedidoActual.detalles?.length || 0} ítems</strong></div>
            </div>
          </div>

          {yaPagado ? (
            <div className="p-4 bg-emerald-950/40 border border-emerald-600/60 rounded-2xl flex items-center gap-3.5 text-emerald-200">
              <CheckCircle2 className="w-7 h-7 text-emerald-400 shrink-0" />
              <div>
                <div className="font-bold text-sm text-emerald-300">Este pedido ya fue pagado</div>
                <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">
                  El cobro ya se encuentra liquidado y registrado en la base de datos de caja. No requiere ninguna confirmación adicional.
                </p>
              </div>
            </div>
          ) : (
            <>
              {/* Selector de Métodos de Pago */}
              <div>
                <label className="block text-xs font-bold text-slate-300 uppercase tracking-wide mb-2">
                  Método de Pago
                </label>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
              <button
                type="button"
                onClick={() => setMetodo('EFECTIVO')}
                className={`flex flex-col items-center justify-center p-2.5 rounded-xl border transition cursor-pointer ${
                  metodo === 'EFECTIVO'
                    ? 'bg-emerald-950/80 border-emerald-500 text-emerald-300 font-bold shadow-lg'
                    : 'bg-slate-800/60 border-slate-700/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <DollarSign className="w-5 h-5 mb-1" />
                <span className="text-xs">Efectivo</span>
              </button>

              <button
                type="button"
                onClick={() => setMetodo('TARJETA')}
                className={`flex flex-col items-center justify-center p-2.5 rounded-xl border transition cursor-pointer ${
                  metodo === 'TARJETA'
                    ? 'bg-sky-950/80 border-sky-500 text-sky-300 font-bold shadow-lg'
                    : 'bg-slate-800/60 border-slate-700/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <CreditCard className="w-5 h-5 mb-1" />
                <span className="text-xs">Tarjeta</span>
              </button>

              <button
                type="button"
                onClick={() => setMetodo('TRANSFERENCIA')}
                className={`flex flex-col items-center justify-center p-2.5 rounded-xl border transition cursor-pointer ${
                  metodo === 'TRANSFERENCIA'
                    ? 'bg-indigo-950/80 border-indigo-500 text-indigo-300 font-bold shadow-lg'
                    : 'bg-slate-800/60 border-slate-700/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <QrCode className="w-5 h-5 mb-1" />
                <span className="text-xs">Nequi/QR</span>
              </button>

              {pedidoActual.canal === 'DIDI' && (
                <button
                  type="button"
                  onClick={() => setMetodo('DIDI_TARJETA')}
                  className={`flex flex-col items-center justify-center p-2.5 rounded-xl border transition cursor-pointer ${
                    metodo === 'DIDI_TARJETA' || metodo === 'DIDI_EFECTIVO'
                      ? 'bg-orange-950/80 border-orange-500 text-orange-300 font-bold shadow-lg'
                      : 'bg-slate-800/60 border-slate-700/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  <ShoppingBag className="w-5 h-5 mb-1" />
                  <span className="text-xs">DiDi Food</span>
                </button>
              )}

              <button
                type="button"
                onClick={() => setMetodo('VALE')}
                className={`flex flex-col items-center justify-center p-2.5 rounded-xl border transition cursor-pointer ${
                  metodo === 'VALE'
                    ? 'bg-purple-950/80 border-purple-500 text-purple-300 font-bold shadow-lg'
                    : 'bg-slate-800/60 border-slate-700/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <FileText className="w-5 h-5 mb-1" />
                <span className="text-xs">Vale (Pagaré)</span>
              </button>

              <button
                type="button"
                onClick={() => setMetodo('MIXTO')}
                className={`flex flex-col items-center justify-center p-2.5 rounded-xl border transition cursor-pointer ${
                  metodo === 'MIXTO'
                    ? 'bg-amber-950/80 border-amber-500 text-amber-300 font-bold shadow-lg'
                    : 'bg-slate-800/60 border-slate-700/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <Layers className="w-5 h-5 mb-1" />
                <span className="text-xs">Mixto</span>
              </button>
            </div>
          </div>

          {/* Formulario Específico según Método */}
          {metodo === 'EFECTIVO' && (
            <div className="bg-slate-950/70 border border-slate-800/80 rounded-2xl p-4 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">
                  Efectivo Recibido del Cliente
                </label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 font-bold text-lg">$</span>
                  <input
                    type="number"
                    min="0"
                    step="1000"
                    value={recibidoEfectivo || ''}
                    onChange={(e) => setRecibidoEfectivo(Number(e.target.value))}
                    className="w-full pl-9 pr-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-emerald-400 font-mono font-bold text-2xl focus:border-emerald-500 focus:outline-none"
                    placeholder="0"
                  />
                </div>
              </div>

              {/* Botones de sugerencia rápida */}
              <div className="flex flex-wrap gap-2">
                {botonesEfectivo.map((btn, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setRecibidoEfectivo(btn.val)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition border cursor-pointer ${
                      recibidoEfectivo === btn.val
                        ? 'bg-emerald-600 border-emerald-500 text-white'
                        : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    {btn.label}
                  </button>
                ))}
              </div>

              {/* Cálculo en Vivo del Cambio */}
              <div
                className={`p-3.5 rounded-xl border flex items-center justify-between ${
                  faltaEfectivo > 0
                    ? 'bg-rose-950/40 border-rose-800 text-rose-300'
                    : 'bg-emerald-950/60 border-emerald-800 text-emerald-300'
                }`}
              >
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider block">
                    {faltaEfectivo > 0 ? 'Faltante por Pagar' : 'Cambio a Devolver'}
                  </span>
                  <div className="text-2xl font-black font-mono">
                    ${(faltaEfectivo > 0 ? faltaEfectivo : cambioEfectivo).toLocaleString('es-CO')} COP
                  </div>
                </div>
                {faltaEfectivo === 0 && (
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 opacity-80" />
                )}
              </div>
            </div>
          )}

          {metodo === 'TARJETA' && (
            <div className="bg-slate-950/70 border border-slate-800/80 rounded-2xl p-4 space-y-3">
              <p className="text-xs text-slate-400">
                Cobro mediante terminal Datáfono Redeban / Bold. Ingresa el código de aprobación o referencia del voucher para conciliación al cierre.
              </p>
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">
                  Número de Aprobación / Voucher Redeban (Opcional)
                </label>
                <input
                  type="text"
                  value={refTarjeta}
                  onChange={(e) => setRefTarjeta(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white font-mono text-sm focus:border-sky-500 focus:outline-none"
                  placeholder="Ej: 045812"
                />
              </div>
            </div>
          )}

          {metodo === 'TRANSFERENCIA' && (
            <div className="bg-slate-950/70 border border-slate-800/80 rounded-2xl p-4 space-y-3">
              <p className="text-xs text-slate-400">
                Verifica en la app de Nequi / Daviplata que el abono se haya reflejado con éxito antes de despachar.
              </p>
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">
                  Referencia de Transferencia (Opcional)
                </label>
                <input
                  type="text"
                  value={refTransferencia}
                  onChange={(e) => setRefTransferencia(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white font-mono text-sm focus:border-indigo-500 focus:outline-none"
                  placeholder="Ej: M1283901"
                />
              </div>
            </div>
          )}

          {(metodo === 'DIDI_TARJETA' || metodo === 'DIDI_EFECTIVO') && (
            <div className="bg-slate-950/70 border border-slate-800/80 rounded-2xl p-4 space-y-3">
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setMetodo('DIDI_TARJETA')}
                  className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold border transition cursor-pointer ${
                    metodo === 'DIDI_TARJETA'
                      ? 'bg-orange-600 border-orange-500 text-white'
                      : 'bg-slate-800 border-slate-700 text-slate-300'
                  }`}
                >
                  💳 DiDi Tarjeta (App)
                </button>
                <button
                  type="button"
                  onClick={() => setMetodo('DIDI_EFECTIVO')}
                  className={`flex-1 py-2 px-3 rounded-xl text-xs font-bold border transition cursor-pointer ${
                    metodo === 'DIDI_EFECTIVO'
                      ? 'bg-orange-600 border-orange-500 text-white'
                      : 'bg-slate-800 border-slate-700 text-slate-300'
                  }`}
                >
                  💵 DiDi Efectivo (Repartidor)
                </button>
              </div>
              <p className="text-xs text-slate-400">
                Orden DiDi: <strong>{pedidoActual.didi_orden_id || 'ID Automático'}</strong>
              </p>
            </div>
          )}

          {metodo === 'VALE' && (
            <div className="bg-slate-950/70 border border-slate-800/80 rounded-2xl p-4 space-y-3">
              <div className="p-3 bg-purple-950/40 border border-purple-800/60 rounded-xl text-xs text-purple-200">
                Se registrará un <strong>pagaré a crédito personal</strong> por ${total.toLocaleString()} COP que quedará pendiente en caja hasta su cobro futuro.
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">
                  Nombre del Cliente / Responsable <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  value={valeNombre}
                  onChange={(e) => setValeNombre(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:border-purple-500 focus:outline-none"
                  placeholder="Ej: Abraham (Empleado) o Juan 66"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    Cédula / Identificación
                  </label>
                  <input
                    type="text"
                    value={valeCedula}
                    onChange={(e) => setValeCedula(e.target.value)}
                    className="w-full px-3.5 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:border-purple-500 focus:outline-none"
                    placeholder="Opcional"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    Teléfono
                  </label>
                  <input
                    type="text"
                    value={valeTelefono}
                    onChange={(e) => setValeTelefono(e.target.value)}
                    className="w-full px-3.5 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:border-purple-500 focus:outline-none"
                    placeholder="Opcional"
                  />
                </div>
              </div>
            </div>
          )}

          {metodo === 'MIXTO' && (
            <div className="bg-slate-950/70 border border-slate-800/80 rounded-2xl p-4 space-y-4">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Distribución de Medios:</span>
                <span className={`font-mono font-bold ${diferenciaMixto === 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {diferenciaMixto === 0
                    ? '✓ Cuadre Exacto'
                    : `Faltan $${Math.abs(diferenciaMixto).toLocaleString()} COP por asignar`}
                </span>
              </div>

              {lineasMixtas.map((linea, index) => (
                <div key={index} className="grid grid-cols-12 gap-2 items-center bg-slate-900 p-2.5 rounded-xl border border-slate-800">
                  <div className="col-span-5">
                    <select
                      value={linea.metodo}
                      onChange={(e) => {
                        const nuevo = [...lineasMixtas]
                        nuevo[index].metodo = e.target.value as MetodoPago
                        setLineasMixtas(nuevo)
                      }}
                      className="w-full py-1.5 px-2 bg-slate-950 border border-slate-700 rounded-lg text-xs font-semibold text-white focus:outline-none"
                    >
                      <option value="EFECTIVO">Efectivo</option>
                      <option value="TARJETA">Tarjeta</option>
                      <option value="TRANSFERENCIA">Transferencia</option>
                    </select>
                  </div>
                  <div className="col-span-6">
                    <input
                      type="number"
                      step="1000"
                      value={linea.monto || ''}
                      onChange={(e) => {
                        const nuevo = [...lineasMixtas]
                        nuevo[index].monto = Number(e.target.value)
                        if (nuevo[index].metodo === 'EFECTIVO') nuevo[index].recibido = Number(e.target.value)
                        setLineasMixtas(nuevo)
                      }}
                      className="w-full py-1.5 px-2 bg-slate-950 border border-slate-700 rounded-lg text-emerald-400 font-mono font-bold text-sm focus:outline-none"
                      placeholder="Monto"
                    />
                  </div>
                  <div className="col-span-1 text-center">
                    {lineasMixtas.length > 2 && (
                      <button
                        type="button"
                        onClick={() => setLineasMixtas(lineasMixtas.filter((_, i) => i !== index))}
                        className="text-slate-500 hover:text-rose-400 cursor-pointer"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}

              <button
                type="button"
                onClick={() => setLineasMixtas([...lineasMixtas, { metodo: 'TRANSFERENCIA', monto: 0 }])}
                className="text-xs font-bold text-amber-400 hover:text-amber-300 cursor-pointer"
              >
                + Agregar otro medio de pago
              </button>
            </div>
          )}
            </>
          )}
        </div>

        {/* Pie de Acciones */}
        <div className="p-4 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2.5 rounded-xl text-xs font-bold text-slate-400 hover:text-white transition cursor-pointer"
          >
            {yaPagado ? 'Cerrar' : 'Cancelar'}
          </button>

          {!yaPagado && (
            <button
              type="button"
              disabled={loading || (metodo === 'EFECTIVO' && faltaEfectivo > 0) || (metodo === 'MIXTO' && diferenciaMixto !== 0)}
              onClick={handleCobrar}
              className="flex items-center gap-2 px-6 py-3 rounded-2xl font-black text-sm bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white shadow-xl shadow-emerald-950/50 transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <CheckCircle2 className="w-5 h-5" />
              )}
              <span>Confirmar Cobro (${total.toLocaleString('es-CO')})</span>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
