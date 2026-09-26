import React, { useState } from 'react'
import type { CierreOut, ConteoBilletesMonedas } from '../../types/caja'
import { cerrarTurno } from '../../api/caja'
import {
  Lock,
  X,
  Calculator,
  Coins,
  Receipt,
  Printer,
  Loader2,
  ShieldCheck,
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
  const [conteo, setConteo] = useState<ConteoBilletesMonedas>({
    b100k: 0,
    b50k: 0,
    b20k: 0,
    b10k: 0,
    b5k: 0,
    b2k: 0,
    m1000: 0,
    m500: 0,
    m200: 0,
    m100: 0,
    m50: 0,
    totalVouchersRedeban: 0,
  })
  const [notas, setNotas] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cierreFinal, setCierreFinal] = useState<CierreOut | null>(null)
  const [isTirillaOpen, setIsTirillaOpen] = useState(false)

  if (!isOpen || !turno) return null

  // Cálculo del efectivo físico contado
  const totalEfectivoContado =
    conteo.b100k * 100000 +
    conteo.b50k * 50000 +
    conteo.b20k * 20000 +
    conteo.b10k * 10000 +
    conteo.b5k * 5000 +
    conteo.b2k * 2000 +
    conteo.m1000 * 1000 +
    conteo.m500 * 500 +
    conteo.m200 * 200 +
    conteo.m100 * 100 +
    conteo.m50 * 50

  const handleCerrarTurno = async () => {
    try {
      setLoading(true)
      setError(null)
      const notaCierre = `Arqueo ciego físico: $${totalEfectivoContado.toLocaleString()} COP | Redeban vouchers: $${conteo.totalVouchersRedeban.toLocaleString()} COP. ${notas}`
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

  // Cálculos de discrepancia (solo visibles en paso RESULTADO)
  const teoricoEfectivo = Number(cierreFinal?.total_efectivo_final || 0)
  const diferenciaEfectivo = totalEfectivoContado - teoricoEfectivo

  const teoricoTarjeta = Number(cierreFinal?.total_tarjeta || 0)
  const diferenciaTarjeta = conteo.totalVouchersRedeban - teoricoTarjeta

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
                  <ShieldCheck className="w-4 h-4" /> Principio de Arqueo a Ciegas
                </strong>
                Cuenta físicamente el dinero en efectivo de la caja y los comprobantes del datáfono <strong>sin conocer el total del sistema</strong>. El sistema comparará tu conteo contra las ventas para determinar si hay cuadre exacto, sobrante o faltante.
              </div>

              {/* Conteo de Billetes */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Coins className="w-4 h-4 text-amber-400" /> Billetes en Gaveta
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  {[
                    { label: '$100.000', key: 'b100k' },
                    { label: '$50.000', key: 'b50k' },
                    { label: '$20.000', key: 'b20k' },
                    { label: '$10.000', key: 'b10k' },
                    { label: '$5.000', key: 'b5k' },
                    { label: '$2.000', key: 'b2k' },
                  ].map((item) => (
                    <div key={item.key} className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-300 font-mono">{item.label}</span>
                      <input
                        type="number"
                        min="0"
                        value={(conteo as any)[item.key] || ''}
                        onChange={(e) =>
                          setConteo({ ...conteo, [item.key]: Math.max(0, parseInt(e.target.value) || 0) })
                        }
                        className="w-16 px-2 py-1 bg-slate-900 border border-slate-700 rounded-lg text-amber-400 font-mono font-bold text-right text-sm focus:outline-none focus:border-amber-500"
                        placeholder="0"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Conteo de Monedas */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Coins className="w-4 h-4 text-slate-400" /> Monedas en Gaveta
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                  {[
                    { label: '$1.000', key: 'm1000' },
                    { label: '$500', key: 'm500' },
                    { label: '$200', key: 'm200' },
                    { label: '$100', key: 'm100' },
                    { label: '$50', key: 'm50' },
                  ].map((item) => (
                    <div key={item.key} className="bg-slate-950 p-2 rounded-xl border border-slate-800 flex items-center justify-between">
                      <span className="text-[11px] font-bold text-slate-400 font-mono">{item.label}</span>
                      <input
                        type="number"
                        min="0"
                        value={(conteo as any)[item.key] || ''}
                        onChange={(e) =>
                          setConteo({ ...conteo, [item.key]: Math.max(0, parseInt(e.target.value) || 0) })
                        }
                        className="w-12 px-1.5 py-1 bg-slate-900 border border-slate-700 rounded-lg text-slate-300 font-mono font-bold text-right text-xs focus:outline-none"
                        placeholder="0"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Total Físico Calculado */}
              <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4 flex items-center justify-between">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Total Efectivo Físico Contado:
                </span>
                <span className="text-2xl font-black text-emerald-400 font-mono">
                  ${totalEfectivoContado.toLocaleString('es-CO')} COP
                </span>
              </div>

              {/* Conciliación Redeban / Datáfono */}
              <div className="bg-slate-950/70 border border-slate-800 rounded-2xl p-4 space-y-2">
                <div className="flex items-center gap-2">
                  <Receipt className="w-4 h-4 text-sky-400" />
                  <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Cierre Datáfono Redeban (Suma de Vouchers $)
                  </label>
                </div>
                <p className="text-[11px] text-slate-400">
                  Ingresa el total acumulado que arrojó el reporte de cierre del datáfono físico.
                </p>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 font-bold">$</span>
                  <input
                    type="number"
                    min="0"
                    step="1000"
                    value={conteo.totalVouchersRedeban || ''}
                    onChange={(e) =>
                      setConteo({ ...conteo, totalVouchersRedeban: Number(e.target.value) })
                    }
                    className="w-full pl-8 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sky-400 font-mono font-bold text-lg focus:border-sky-500 focus:outline-none"
                    placeholder="0"
                  />
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
              {/* Veredicto de Cuadre */}
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
                <div className="text-3xl font-black font-mono">
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

              {/* Conciliación Redeban */}
              <div
                className={`p-3.5 rounded-xl border flex items-center justify-between text-xs ${
                  diferenciaTarjeta === 0
                    ? 'bg-slate-950 border-slate-800 text-slate-300'
                    : 'bg-amber-950/40 border-amber-700 text-amber-300'
                }`}
              >
                <div>
                  <strong className="block">Conciliación Datáfono Redeban</strong>
                  <span>Vouchers Contados: ${conteo.totalVouchersRedeban.toLocaleString()} COP • Sistema: ${teoricoTarjeta.toLocaleString()} COP</span>
                </div>
                <span className="font-mono font-bold">
                  {diferenciaTarjeta === 0 ? '✓ Conciliado' : `Dif: $${diferenciaTarjeta.toLocaleString()} COP`}
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
                    <span className="text-white">${Number(cierreFinal.total_venta_comida).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Venta Bebida:</span>
                    <span className="text-white">${Number(cierreFinal.total_venta_bebida).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between font-bold text-amber-400 pt-1 border-t border-slate-900">
                    <span>TOTAL VENTAS FACTURADAS:</span>
                    <span>${Number(cierreFinal.total_ventas).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-slate-400 pt-2 border-t border-slate-900">
                    <span>Total Efectivo Recaudado:</span>
                    <span className="text-emerald-400">${Number(cierreFinal.total_efectivo).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Total Tarjeta / Redeban:</span>
                    <span className="text-sky-400">${Number(cierreFinal.total_tarjeta).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Total Transferencias QR:</span>
                    <span className="text-indigo-400">${Number(cierreFinal.total_transferencia).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Total DiDi Food:</span>
                    <span className="text-orange-400">${(Number(cierreFinal.total_didi_tarjeta) + Number(cierreFinal.total_didi_efectivo)).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Vales a Crédito ({cierreFinal.cantidad_vales}):</span>
                    <span className="text-purple-400">${Number(cierreFinal.total_vale).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-slate-400 pt-2 border-t border-slate-900">
                    <span>Entradas Caja Menor:</span>
                    <span className="text-emerald-400">+${Number(cierreFinal.total_entradas_caja).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Salidas Caja Menor (Egresos):</span>
                    <span className="text-rose-400">-${Number(cierreFinal.total_salidas_caja).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between font-black text-white text-sm pt-2 border-t border-slate-800">
                    <span>EFECTIVO FINAL ESPERADO EN CAJA:</span>
                    <span className="text-emerald-400">${Number(cierreFinal.total_efectivo_final).toLocaleString()}</span>
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
            notas: cierreFinal.notas || undefined
          }}
        />
      )}
    </div>
  )
}
