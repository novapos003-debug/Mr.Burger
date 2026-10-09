import React, { useState, useEffect } from 'react'
import {
  DollarSign,
  Lock,
  Unlock,
  User,
  Printer,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Search,
} from 'lucide-react'
import { getHistorialCierres } from '../../api/caja'
import type { CierreOut } from '../../types/caja'
import { TirillaModal } from '../common/TirillaModal'
import type { DatosReporteZ } from '../../utils/printer'

export const CierresCajaTab: React.FC = () => {
  const [cierres, setCierres] = useState<CierreOut[]>([])
  const [loading, setLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [filtroTexto, setFiltroTexto] = useState('')
  const [reporteZSel, setReporteZSel] = useState<DatosReporteZ | null>(null)
  const [isTirillaOpen, setIsTirillaOpen] = useState(false)

  const cargarCierres = async (silent = false) => {
    try {
      if (!silent) setLoading(true)
      else setIsRefreshing(true)
      const data = await getHistorialCierres()
      setCierres(data)
    } catch (err) {
      console.error('Error cargando historial de cierres:', err)
    } finally {
      setLoading(false)
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    cargarCierres()
  }, [])

  // Extraer el efectivo declarado del texto de notas si existe
  const extraerEfectivoDeclarado = (c: CierreOut): number => {
    if (!c.notas) return Number(c.total_efectivo_final || 0)
    const match = c.notas.match(/Total Efectivo:\s*\$([0-9.,]+)/)
    if (match && match[1]) {
      const limpio = match[1].replace(/\./g, '').replace(/,/g, '.')
      const num = parseFloat(limpio)
      if (!isNaN(num)) return num
    }
    return Number(c.total_efectivo_final || 0)
  }

  const handleVerTirillaZ = (c: CierreOut) => {
    const declarado = extraerEfectivoDeclarado(c)
    const esperado = Number(c.total_efectivo_final || 0)
    const dif = declarado - esperado
    const base = Number(c.monto_inicial || c.total_entradas_caja || 0)

    const datos: DatosReporteZ = {
      restaurante: 'MR. BURGER',
      turno_id: c.id,
      fecha_apertura: new Date(c.abierto_en).toLocaleString('es-CO'),
      fecha_cierre: c.cerrado_en ? new Date(c.cerrado_en).toLocaleString('es-CO') : 'EN CURSO',
      cajero: c.usuario_nombre || `Cajero #${c.usuario_id}`,
      monto_inicial: base,
      total_ventas: Number(c.total_ventas || 0),
      total_venta_comida: Number(c.total_venta_comida || 0),
      total_venta_bebida: Number(c.total_venta_bebida || 0),
      total_efectivo: Number(c.total_efectivo || 0),
      total_tarjeta: Number(c.total_tarjeta || 0),
      total_transferencia: Number(c.total_transferencia || 0),
      total_didi_tarjeta: Number(c.total_didi_tarjeta || 0),
      total_didi_efectivo: Number(c.total_didi_efectivo || 0),
      total_vale: Number(c.total_vale || 0),
      total_salidas_caja: Number(c.total_salidas_caja || 0),
      total_entradas_caja: Number(c.total_entradas_caja || 0),
      total_devoluciones: Number(c.total_devoluciones || 0),
      efectivo_esperado: esperado,
      efectivo_declarado: declarado,
      diferencia: dif,
      preparados_reutilizados: c.preparados_reutilizados || 0,
      preparados_descartados: c.preparados_descartados || 0,
      notas: c.notas || undefined,
    }

    setReporteZSel(datos)
    setIsTirillaOpen(true)
  }

  // Filtrado de cierres
  const cierresFiltrados = cierres.filter((c) => {
    const q = filtroTexto.trim().toLowerCase()
    if (!q) return true
    const nombre = (c.usuario_nombre || '').toLowerCase()
    const idStr = `#${c.id}`
    const notas = (c.notas || '').toLowerCase()
    return nombre.includes(q) || idStr.includes(q) || notas.includes(q)
  })

  // Turno actualmente abierto (si existe)
  const turnoActivo = cierres.find((c) => !c.cerrado_en)

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-400">
        <RefreshCw className="w-8 h-8 animate-spin text-amber-500 mb-3" />
        <span className="text-sm font-bold">Cargando historial de cierres de caja...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Banner Explicativo de Auditoría */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0">
            <DollarSign className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-black text-white text-base">Cierres de Caja & Reportes Z</h3>
            <p className="text-xs text-slate-400">
              Historial de aperturas, bases iniciales, ventas, arqueos a ciegas y cuadres auditados
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => cargarCierres(true)}
          disabled={isRefreshing}
          className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-bold transition cursor-pointer self-stretch sm:self-auto justify-center"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-amber-400' : ''}`} />
          <span>Actualizar</span>
        </button>
      </div>

      {/* Indicador de Turno Abierto Actual */}
      {turnoActivo ? (
        <div className="bg-gradient-to-r from-emerald-950/70 to-slate-900 border border-emerald-600/50 rounded-2xl p-4 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/50 flex items-center justify-center text-emerald-400 shrink-0">
              <Unlock className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-sm text-white">TURNO #{turnoActivo.id} EN CURSO</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-emerald-950 text-emerald-400 border border-emerald-600">
                  CAJA ABIERTA
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                Cajero: <strong className="text-white">{turnoActivo.usuario_nombre || 'Cajero'}</strong> •
                Abierto a las {new Date(turnoActivo.abierto_en).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', hour12: true })}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto justify-between md:justify-end border-t md:border-t-0 pt-3 md:pt-0 border-slate-800">
            <div className="text-left md:text-right">
              <span className="text-[10px] text-slate-400 uppercase font-bold block">Base de Efectivo:</span>
              <span className="font-mono font-black text-white text-base">
                ${Number(turnoActivo.monto_inicial || turnoActivo.total_entradas_caja || 0).toLocaleString('es-CO')} COP
              </span>
            </div>
            <div className="text-left md:text-right">
              <span className="text-[10px] text-slate-400 uppercase font-bold block">Ventas Turno:</span>
              <span className="font-mono font-black text-emerald-400 text-base">
                ${Number(turnoActivo.total_ventas || 0).toLocaleString('es-CO')} COP
              </span>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2.5">
            <Lock className="w-4 h-4 text-slate-500" />
            <span>Actualmente no hay ningún turno de caja abierto en el restaurante.</span>
          </div>
        </div>
      )}

      {/* Buscador y Contador */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={filtroTexto}
            onChange={(e) => setFiltroTexto(e.target.value)}
            placeholder="Buscar por cajero, turno #..."
            className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-amber-500"
          />
        </div>
        <span className="text-xs text-slate-400 font-medium">
          Total de turnos registrados: <strong className="text-white">{cierres.length}</strong>
        </span>
      </div>

      {/* Tabla de Cierres de Turno */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-bold uppercase tracking-wider text-[11px]">
              <tr>
                <th className="p-3.5">Turno</th>
                <th className="p-3.5">Cajero</th>
                <th className="p-3.5">Apertura</th>
                <th className="p-3.5">Cierre</th>
                <th className="p-3.5 text-right">Base Inicial</th>
                <th className="p-3.5 text-right">Ventas Totales</th>
                <th className="p-3.5 text-right">Efectivo Sistema</th>
                <th className="p-3.5 text-right">Arqueo Declarado</th>
                <th className="p-3.5 text-center">Cuadre</th>
                <th className="p-3.5 text-center">Tirilla Z</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {cierresFiltrados.length === 0 ? (
                <tr>
                  <td colSpan={10} className="p-8 text-center text-slate-500">
                    No se encontraron turnos de caja registrados.
                  </td>
                </tr>
              ) : (
                cierresFiltrados.map((c) => {
                  const declarado = extraerEfectivoDeclarado(c)
                  const esperado = Number(c.total_efectivo_final || 0)
                  const dif = declarado - esperado
                  const base = Number(c.monto_inicial || c.total_entradas_caja || 0)
                  const esAbierto = !c.cerrado_en

                  return (
                    <tr key={c.id} className="hover:bg-slate-800/40 transition">
                      <td className="p-3.5">
                        <span className="font-mono font-black text-white text-xs">#{c.id}</span>
                      </td>

                      <td className="p-3.5">
                        <div className="flex items-center gap-1.5 font-bold text-slate-200">
                          <User className="w-3.5 h-3.5 text-slate-400" />
                          <span>{c.usuario_nombre || `Usuario #${c.usuario_id}`}</span>
                        </div>
                      </td>

                      <td className="p-3.5 text-slate-300 font-mono text-[11px]">
                        {new Date(c.abierto_en).toLocaleString('es-CO', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                          hour12: true,
                        })}
                      </td>

                      <td className="p-3.5 text-slate-300 font-mono text-[11px]">
                        {esAbierto ? (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-black bg-emerald-950 text-emerald-400 border border-emerald-600">
                            En curso
                          </span>
                        ) : (
                          new Date(c.cerrado_en!).toLocaleString('es-CO', {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                            hour12: true,
                          })
                        )}
                      </td>

                      <td className="p-3.5 text-right font-mono font-bold text-amber-400">
                        ${base.toLocaleString('es-CO')}
                      </td>

                      <td className="p-3.5 text-right font-mono font-bold text-slate-200">
                        ${Number(c.total_ventas || 0).toLocaleString('es-CO')}
                      </td>

                      <td className="p-3.5 text-right font-mono font-bold text-slate-300">
                        ${esperado.toLocaleString('es-CO')}
                      </td>

                      <td className="p-3.5 text-right font-mono font-bold text-emerald-400">
                        {esAbierto ? '--' : `$${declarado.toLocaleString('es-CO')}`}
                      </td>

                      <td className="p-3.5 text-center">
                        {esAbierto ? (
                          <span className="text-slate-500 font-mono text-[11px]">--</span>
                        ) : Math.abs(dif) === 0 ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-black bg-emerald-950 text-emerald-400 border border-emerald-600">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Exacto ($0)</span>
                          </span>
                        ) : dif > 0 ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-black bg-sky-950 text-sky-400 border border-sky-600">
                            <span>+${dif.toLocaleString('es-CO')} Sobra</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-black bg-rose-950 text-rose-400 border border-rose-600">
                            <AlertTriangle className="w-3 h-3" />
                            <span>-${Math.abs(dif).toLocaleString('es-CO')} Falta</span>
                          </span>
                        )}
                      </td>

                      <td className="p-3.5 text-center">
                        <button
                          type="button"
                          onClick={() => handleVerTirillaZ(c)}
                          className="px-2.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-sky-400 hover:text-white border border-slate-700 font-bold text-[11px] transition flex items-center justify-center gap-1 mx-auto cursor-pointer"
                          title="Ver tirilla oficial del Reporte Z e imprimir"
                        >
                          <Printer className="w-3.5 h-3.5" />
                          <span>Ver Z</span>
                        </button>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Tirilla Modal para Reporte Z */}
      {reporteZSel && (
        <TirillaModal
          isOpen={isTirillaOpen}
          onClose={() => {
            setIsTirillaOpen(false)
            setReporteZSel(null)
          }}
          tipo="REPORTE_Z"
          datosReporteZ={reporteZSel}
        />
      )}
    </div>
  )
}
