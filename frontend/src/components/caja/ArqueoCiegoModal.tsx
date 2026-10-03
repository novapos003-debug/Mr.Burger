import React, { useState } from 'react'
import type { CierreOut } from '../../types/caja'
import { cerrarTurno } from '../../api/caja'
import {
  Lock,
  X,
  Calculator,
  Coins,
  Banknote,
  CreditCard,
  Printer,
  Loader2,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
} from 'lucide-react'

import { TirillaModal } from '../common/TirillaModal'

interface Props {
  isOpen: boolean
  turno: CierreOut | null
  onClose: () => void
  onTurnoCerrado: (cierreResultado: CierreOut) => void
}

export const ArqueoCiegoModal: React.FC<Props> = ({
  isOpen,
  turno,
  onClose,
  onTurnoCerrado,
}) => {
  const [paso, setPaso] = useState<'CONTEO' | 'RESULTADO'>('CONTEO')
  const [totalBilletes, setTotalBilletes] = useState<number>(0)
  const [totalMonedas, setTotalMonedas] = useState<number>(0)
  const [totalElectronico, setTotalElectronico] = useState<number>(0)
  const [mostrarDesglose, setMostrarDesglose] = useState<boolean>(false)

  const [conteoBilletes, setConteoBilletes] = useState({
    b100k: 0,
    b50k: 0,
    b20k: 0,
    b10k: 0,
    b5k: 0,
    b2k: 0,
  })
  const [conteoMonedas, setConteoMonedas] = useState({
    m1000: 0,
    m500: 0,
    m200: 0,
    m100: 0,
    m50: 0,
  })

  const [notas, setNotas] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cierreFinal, setCierreFinal] = useState<CierreOut | null>(null)
  const [isTirillaOpen, setIsTirillaOpen] = useState(false)

  if (!isOpen || !turno) return null

  // Métricas del sistema en tiempo real para datáfono y transferencias
  const esperadoTarjeta = Number(turno.total_tarjeta || 0)
  const esperadoTransferencia = Number(turno.total_transferencia || 0)
  const totalEsperadoElectronico = esperadoTarjeta + esperadoTransferencia

  // Total de efectivo físico contado
  const totalEfectivoContado = (Number(totalBilletes) || 0) + (Number(totalMonedas) || 0)

  // Recalcular billetes si cambia el desglose individual
  const handleCambioBilletes = (key: string, val: number) => {
    const updated = { ...conteoBilletes, [key]: val }
    setConteoBilletes(updated)
    const nuevoTotal =
      updated.b100k * 100000 +
      updated.b50k * 50000 +
      updated.b20k * 20000 +
      updated.b10k * 10000 +
      updated.b5k * 5000 +
      updated.b2k * 2000
    setTotalBilletes(nuevoTotal)
  }

  // Recalcular monedas si cambia el desglose individual
  const handleCambioMonedas = (key: string, val: number) => {
    const updated = { ...conteoMonedas, [key]: val }
    setConteoMonedas(updated)
    const nuevoTotal =
      updated.m1000 * 1000 +
      updated.m500 * 500 +
      updated.m200 * 200 +
      updated.m100 * 100 +
      updated.m50 * 50
    setTotalMonedas(nuevoTotal)
  }

  const handleCerrarTurno = async () => {
    try {
      setLoading(true)
      setError(null)
      const notaCierre = `Arqueo físico: Billetes: $${totalBilletes.toLocaleString('es-CO')} COP | Monedas: $${totalMonedas.toLocaleString('es-CO')} COP | Total Efectivo: $${totalEfectivoContado.toLocaleString('es-CO')} COP | Datáfono/Transferencias: $${totalElectronico.toLocaleString('es-CO')} COP. ${notas}`
      const resultado = await cerrarTurno(notaCierre)
      setCierreFinal(resultado)
      setPaso('RESULTADO')
      onTurnoCerrado(resultado)
    } catch (err: any) {
      console.error('Error cerrando turno:', err)
      setError(err.response?.data?.detail || 'Error al cerrar el turno')
    } finally {
      setLoading(false)
    }
  }

  // Cálculos de discrepancia (visibles en paso RESULTADO)
  const teoricoEfectivo = Number(cierreFinal?.total_efectivo_final || 0)
  const diferenciaEfectivo = totalEfectivoContado - teoricoEfectivo

  const teoricoTarjeta = Number(cierreFinal?.total_tarjeta || 0)
  const teoricoTransferencia = Number(cierreFinal?.total_transferencia || 0)
  const teoricoElectronico = teoricoTarjeta + teoricoTransferencia
  const diferenciaElectronico = totalElectronico - teoricoElectronico

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-3 sm:p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Cabecera */}
        <div className="p-4 border-b border-slate-800 bg-slate-800/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-600/30 border border-purple-500/40 flex items-center justify-center text-purple-400">
              <Calculator className="w-6 h-6" />
            </div>
            <div>
              <h2 className="font-black text-white text-lg tracking-wide">
                {paso === 'CONTEO' ? 'Arqueo a Ciegas & Cierre Z' : 'Reporte Z de Cierre Generado'}
              </h2>
              <p className="text-xs text-slate-400">
                Turno #{turno.id} • Abierto el {new Date(turno.abierto_en).toLocaleDateString()} a las {new Date(turno.abierto_en).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
        <div className="p-5 overflow-y-auto space-y-5 flex-1">
          {error && (
            <div className="p-3 bg-rose-950/80 border border-rose-800 text-rose-300 rounded-xl text-xs">
              {error}
            </div>
          )}

          {paso === 'CONTEO' ? (
            <>
              <div className="bg-purple-950/30 border border-purple-800/50 rounded-2xl p-4 text-xs text-purple-200 leading-relaxed">
                <strong className="text-purple-300 flex items-center gap-1.5 mb-1 text-sm font-black">
                  <ShieldCheck className="w-4 h-4" /> Cuadre de Caja Simplificado
                </strong>
                Ingresa el total que tienes en billetes y monedas en la gaveta, y el total de datáfono / transferencias. El sistema contrastará tu conteo contra las ventas para determinar el cuadre exacto.
              </div>

              {/* SECCIÓN 1: EFECTIVO FÍSICO (Billetes y Monedas Directos) */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                    <Banknote className="w-4 h-4 text-emerald-400" />
                    <span>Conteo de Efectivo en Gaveta</span>
                  </h3>
                  <button
                    type="button"
                    onClick={() => setMostrarDesglose(!mostrarDesglose)}
                    className="text-[11px] font-bold text-slate-400 hover:text-amber-400 flex items-center gap-1 transition cursor-pointer"
                  >
                    {mostrarDesglose ? (
                      <>
                        <ChevronUp className="w-3.5 h-3.5" />
                        <span>Ocultar desglose</span>
                      </>
                    ) : (
                      <>
                        <ChevronDown className="w-3.5 h-3.5" />
                        <span>Desglosar denominaciones</span>
                      </>
                    )}
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Total Billetes */}
                  <div className="bg-slate-900/90 border border-slate-700/80 rounded-xl p-3 space-y-1.5">
                    <label className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
                      <Banknote className="w-4 h-4" /> Total en Billetes ($)
                    </label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 font-bold">$</span>
                      <input
                        type="number"
                        min="0"
                        step="1000"
                        value={totalBilletes || ''}
                        onChange={(e) => setTotalBilletes(Math.max(0, parseInt(e.target.value) || 0))}
                        className="w-full pl-8 pr-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-amber-400 font-mono font-bold text-lg focus:border-amber-500 focus:outline-none"
                        placeholder="0"
                      />
                    </div>
                    <div className="text-[11px] text-slate-400 text-right font-mono">
                      ${totalBilletes.toLocaleString('es-CO')} COP
                    </div>
                  </div>

                  {/* Total Monedas */}
                  <div className="bg-slate-900/90 border border-slate-700/80 rounded-xl p-3 space-y-1.5">
                    <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                      <Coins className="w-4 h-4 text-slate-400" /> Total en Monedas ($)
                    </label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 font-bold">$</span>
                      <input
                        type="number"
                        min="0"
                        step="50"
                        value={totalMonedas || ''}
                        onChange={(e) => setTotalMonedas(Math.max(0, parseInt(e.target.value) || 0))}
                        className="w-full pl-8 pr-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-200 font-mono font-bold text-lg focus:border-slate-500 focus:outline-none"
                        placeholder="0"
                      />
                    </div>
                    <div className="text-[11px] text-slate-400 text-right font-mono">
                      ${totalMonedas.toLocaleString('es-CO')} COP
                    </div>
                  </div>
                </div>

                {/* Desglose opcional por denominación */}
                {mostrarDesglose && (
                  <div className="pt-3 border-t border-slate-800 space-y-3 animate-in fade-in duration-150">
                    <div className="space-y-2">
                      <span className="text-[11px] font-bold text-slate-400 block uppercase">
                        Billetes por denominación (calcula el total de billetes):
                      </span>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        {[
                          { label: '$100.000', key: 'b100k' },
                          { label: '$50.000', key: 'b50k' },
                          { label: '$20.000', key: 'b20k' },
                          { label: '$10.000', key: 'b10k' },
                          { label: '$5.000', key: 'b5k' },
                          { label: '$2.000', key: 'b2k' },
                        ].map((item) => (
                          <div key={item.key} className="bg-slate-900 p-2 rounded-lg border border-slate-800 flex items-center justify-between">
                            <span className="text-xs font-bold text-slate-300 font-mono">{item.label}</span>
                            <input
                              type="number"
                              min="0"
                              value={(conteoBilletes as any)[item.key] || ''}
                              onChange={(e) =>
                                handleCambioBilletes(item.key, Math.max(0, parseInt(e.target.value) || 0))
                              }
                              className="w-14 px-1.5 py-1 bg-slate-950 border border-slate-700 rounded text-amber-400 font-mono font-bold text-right text-xs focus:outline-none"
                              placeholder="0"
                            />
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <span className="text-[11px] font-bold text-slate-400 block uppercase">
                        Monedas por denominación (calcula el total de monedas):
                      </span>
                      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                        {[
                          { label: '$1.000', key: 'm1000' },
                          { label: '$500', key: 'm500' },
                          { label: '$200', key: 'm200' },
                          { label: '$100', key: 'm100' },
                          { label: '$50', key: 'm50' },
                        ].map((item) => (
                          <div key={item.key} className="bg-slate-900 p-1.5 rounded-lg border border-slate-800 flex items-center justify-between">
                            <span className="text-[11px] font-bold text-slate-400 font-mono">{item.label}</span>
                            <input
                              type="number"
                              min="0"
                              value={(conteoMonedas as any)[item.key] || ''}
                              onChange={(e) =>
                                handleCambioMonedas(item.key, Math.max(0, parseInt(e.target.value) || 0))
                              }
                              className="w-12 px-1 py-0.5 bg-slate-950 border border-slate-700 rounded text-slate-300 font-mono font-bold text-right text-xs focus:outline-none"
                              placeholder="0"
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Total Efectivo Físico Calculado */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Total Efectivo Físico Contado:
                  </span>
                  <span className="text-xl font-black text-emerald-400 font-mono">
                    ${totalEfectivoContado.toLocaleString('es-CO')} COP
                  </span>
                </div>
              </div>

              {/* SECCIÓN 2: DATÁFONO / TRANSFERENCIAS */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <CreditCard className="w-4 h-4 text-sky-400" />
                  <label className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                    Datáfono / Transferencias (Vouchers y Recibos Bancarios)
                  </label>
                </div>

                {/* Badge informativa con el total esperado por el sistema */}
                <div className="bg-sky-950/40 border border-sky-800/60 rounded-xl p-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5">
                  <div className="text-xs text-sky-200">
                    <span className="font-black text-sky-300 block text-sm">
                      El sistema espera: ${totalEsperadoElectronico.toLocaleString('es-CO')} COP
                    </span>
                    <span className="text-[11px] text-sky-400">
                      Datáfono / Tarjetas: ${esperadoTarjeta.toLocaleString('es-CO')} COP • Transferencias / QR: ${esperadoTransferencia.toLocaleString('es-CO')} COP
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setTotalElectronico(totalEsperadoElectronico)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-sky-600 hover:bg-sky-500 active:scale-95 text-white cursor-pointer transition whitespace-nowrap shadow shrink-0"
                    title="Copia el monto esperado por el sistema directamente al campo de cierre"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Usar total esperado (${totalEsperadoElectronico.toLocaleString('es-CO')})</span>
                  </button>
                </div>

                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 font-bold">$</span>
                  <input
                    type="number"
                    min="0"
                    step="1000"
                    value={totalElectronico || ''}
                    onChange={(e) => setTotalElectronico(Math.max(0, parseInt(e.target.value) || 0))}
                    className="w-full pl-8 pr-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-sky-400 font-mono font-bold text-lg focus:border-sky-500 focus:outline-none"
                    placeholder="0"
                  />
                </div>
                <div className="text-[11px] text-slate-400 text-right font-mono">
                  ${totalElectronico.toLocaleString('es-CO')} COP
                </div>
              </div>

              {/* Notas del Cierre */}
              <div>
                <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1">
                  Observaciones / Novedades del Turno (Opcional)
                </label>
                <textarea
                  rows={2}
                  value={notas}
                  onChange={(e) => setNotas(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none"
                  placeholder="Ej: Turno tranquilo sin novedades. Cuadre verificado con supervisor."
                />
              </div>
            </>
          ) : (
            /* PASO RESULTADO: REPORTE Z DE CIERRE */
            <div className="space-y-4">
              {/* Veredicto de Cuadre Efectivo */}
              <div
                className={`p-4 rounded-2xl border text-center ${
                  diferenciaEfectivo === 0
                    ? 'bg-emerald-950/60 border-emerald-500 text-emerald-300'
                    : diferenciaEfectivo > 0
                    ? 'bg-amber-950/60 border-amber-500 text-amber-300'
                    : 'bg-rose-950/60 border-rose-500 text-rose-300'
                }`}
              >
                <span className="text-xs font-bold uppercase tracking-widest block mb-1">
                  Resultado del Arqueo de Efectivo
                </span>
                <div className="text-2xl sm:text-3xl font-black font-mono">
                  {diferenciaEfectivo === 0
                    ? '✓ CUADRE EXACTO ($0 COP)'
                    : diferenciaEfectivo > 0
                    ? `SOBRANTE: +$${diferenciaEfectivo.toLocaleString('es-CO')} COP`
                    : `FALTANTE: -$${Math.abs(diferenciaEfectivo).toLocaleString('es-CO')} COP`}
                </div>
                <p className="text-xs mt-1 opacity-80">
                  Físico Contado: ${totalEfectivoContado.toLocaleString('es-CO')} COP vs Sistema Teórico: ${teoricoEfectivo.toLocaleString('es-CO')} COP
                </p>
              </div>

              {/* Conciliación Datáfono / Transferencias */}
              <div
                className={`p-3.5 rounded-xl border flex items-center justify-between text-xs ${
                  diferenciaElectronico === 0
                    ? 'bg-slate-950 border-slate-800 text-slate-300'
                    : 'bg-amber-950/40 border-amber-700 text-amber-300'
                }`}
              >
                <div>
                  <strong className="block">Conciliación Datáfono / Transferencias</strong>
                  <span>Declarado: ${totalElectronico.toLocaleString('es-CO')} COP • Sistema: ${teoricoElectronico.toLocaleString('es-CO')} COP</span>
                </div>
                <span className="font-mono font-bold">
                  {diferenciaElectronico === 0
                    ? '✓ Conciliado'
                    : `Dif: ${diferenciaElectronico > 0 ? '+' : ''}$${diferenciaElectronico.toLocaleString('es-CO')} COP`}
                </span>
              </div>

              {/* Desglose de Ventas del Turno */}
              {cierreFinal && (
                <div className="bg-slate-950 rounded-2xl border border-slate-800 p-4 text-xs space-y-2 font-mono">
                  <div className="flex justify-between border-b border-slate-800/80 pb-1.5 font-bold text-slate-300 font-sans">
                    <span>CONCEPTO FINANCIERO</span>
                    <span>IMPORTE COP</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Venta Comida (Alimentos):</span>
                    <span className="text-white">${Number(cierreFinal.total_venta_comida).toLocaleString('es-CO')}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Venta Bebida:</span>
                    <span className="text-white">${Number(cierreFinal.total_venta_bebida).toLocaleString('es-CO')}</span>
                  </div>
                  <div className="flex justify-between font-bold text-amber-400 pt-1 border-t border-slate-900">
                    <span>TOTAL VENTAS FACTURADAS:</span>
                    <span>${Number(cierreFinal.total_ventas).toLocaleString('es-CO')}</span>
                  </div>
                  <div className="flex justify-between text-slate-400 pt-2 border-t border-slate-900">
                    <span>Total Efectivo Recaudado:</span>
                    <span className="text-emerald-400">${Number(cierreFinal.total_efectivo).toLocaleString('es-CO')}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Total Tarjeta / Datáfono:</span>
                    <span className="text-sky-400">${Number(cierreFinal.total_tarjeta).toLocaleString('es-CO')}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Total Transferencias QR:</span>
                    <span className="text-indigo-400">${Number(cierreFinal.total_transferencia).toLocaleString('es-CO')}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Total DiDi Food:</span>
                    <span className="text-orange-400">${(Number(cierreFinal.total_didi_tarjeta) + Number(cierreFinal.total_didi_efectivo)).toLocaleString('es-CO')}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Vales a Crédito ({cierreFinal.cantidad_vales}):</span>
                    <span className="text-purple-400">${Number(cierreFinal.total_vale).toLocaleString('es-CO')}</span>
                  </div>
                  <div className="flex justify-between text-slate-400 pt-2 border-t border-slate-900">
                    <span>Entradas Caja Menor:</span>
                    <span className="text-emerald-400">+${Number(cierreFinal.total_entradas_caja).toLocaleString('es-CO')}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Salidas Caja Menor (Egresos):</span>
                    <span className="text-rose-400">-${Number(cierreFinal.total_salidas_caja).toLocaleString('es-CO')}</span>
                  </div>
                  <div className="flex justify-between font-black text-white text-sm pt-2 border-t border-slate-800">
                    <span>EFECTIVO FINAL ESPERADO EN CAJA:</span>
                    <span className="text-emerald-400">${Number(cierreFinal.total_efectivo_final).toLocaleString('es-CO')}</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Pie de Acciones */}
        <div className="p-4 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between gap-3">
          {paso === 'CONTEO' ? (
            <>
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 rounded-xl text-xs font-bold text-slate-400 hover:text-white transition cursor-pointer"
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={loading}
                onClick={handleCerrarTurno}
                className="flex items-center gap-2 px-6 py-3 rounded-2xl font-black text-sm bg-purple-600 hover:bg-purple-500 active:scale-95 text-white shadow-xl shadow-purple-950/50 transition cursor-pointer disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Lock className="w-5 h-5" />
                )}
                <span>Confirmar Arqueo y Cerrar Turno</span>
              </button>
            </>
          ) : (
            <>
              <div className="text-xs text-slate-500">
                Fotograma congelado en la base de datos de auditoría.
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsTirillaOpen(true)}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 cursor-pointer transition"
                >
                  <Printer className="w-4 h-4 text-amber-400" />
                  <span>Imprimir Reporte Z</span>
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="px-5 py-2.5 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 text-white cursor-pointer transition"
                >
                  Finalizar
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {cierreFinal && (
        <TirillaModal
          isOpen={isTirillaOpen}
          onClose={() => setIsTirillaOpen(false)}
          tipo="REPORTE_Z"
          datosReporteZ={{
            restaurante: 'MR. BURGER',
            turno_id: cierreFinal.id,
            fecha_apertura: new Date(cierreFinal.abierto_en).toLocaleString('es-CO'),
            fecha_cierre: new Date(cierreFinal.cerrado_en || new Date()).toLocaleString('es-CO'),
            cajero: 'Caja Principal',
            monto_inicial: Number(cierreFinal.total_entradas_caja || 0),
            total_ventas: Number(cierreFinal.total_ventas),
            total_venta_comida: Number(cierreFinal.total_venta_comida || 0),
            total_venta_bebida: Number(cierreFinal.total_venta_bebida || 0),
            total_efectivo: Number(cierreFinal.total_efectivo),
            total_tarjeta: Number(cierreFinal.total_tarjeta),
            total_transferencia: Number(cierreFinal.total_transferencia),
            total_didi_tarjeta: Number(cierreFinal.total_didi_tarjeta),
            total_didi_efectivo: Number(cierreFinal.total_didi_efectivo),
            total_vale: Number(cierreFinal.total_vale),
            total_salidas_caja: Number(cierreFinal.total_salidas_caja),
            total_entradas_caja: Number(cierreFinal.total_entradas_caja),
            total_devoluciones: Number(cierreFinal.total_devoluciones || 0),
            efectivo_esperado: Number(cierreFinal.total_efectivo_final),
            efectivo_declarado: totalEfectivoContado,
            diferencia: totalEfectivoContado - Number(cierreFinal.total_efectivo_final),
            preparados_reutilizados: cierreFinal.preparados_reutilizados || 0,
            preparados_descartados: cierreFinal.preparados_descartados || 0,
            notas: cierreFinal.notas || undefined,
          }}
        />
      )}
    </div>
  )
}
