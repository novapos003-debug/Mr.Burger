import React, { useState, useEffect } from 'react'
import {
  Clock,
  LogOut,
  History,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react'
import { getTurnosActivosApi, getTurnosHistorialApi, cerrarTurnoAdminApi } from '../../api/asistencia'
import type { TurnoLaboral } from '../../types/asistencia'

export const AsistenciaTab: React.FC = () => {
  const [activos, setActivos] = useState<TurnoLaboral[]>([])
  const [historial, setHistorial] = useState<TurnoLaboral[]>([])
  const [loading, setLoading] = useState(true)

  const cargarDatos = async () => {
    try {
      setLoading(true)
      const [act, hist] = await Promise.all([
        getTurnosActivosApi(),
        getTurnosHistorialApi(),
      ])
      setActivos(act)
      setHistorial(hist)
    } catch (err) {
      console.error('Error cargando asistencia:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    cargarDatos()
  }, [])

  const handleCerrarTurno = async (id: number) => {
    if (!window.confirm('¿Cerrar manualmente este turno?')) return
    try {
      await cerrarTurnoAdminApi(id)
      cargarDatos()
    } catch (err) {
      alert('Error cerrando turno')
    }
  }

  const calcularDuracion = (entrada: string, salida: string | null) => {
    const d1 = new Date(entrada)
    const d2 = salida ? new Date(salida) : new Date()
    const diffMs = d2.getTime() - d1.getTime()
    const horas = Math.floor(diffMs / 3600000)
    const minutos = Math.floor((diffMs % 3600000) / 60000)
    return `${horas}h ${minutos}m`
  }

  const formatearFechaHora = (isoStr: string) => {
    const d = new Date(isoStr)
    return d.toLocaleString('es-CO', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true
    })
  }

  if (loading) {
    return (
      <div className="flex justify-center p-8 text-slate-400">
        <RefreshCw className="w-6 h-6 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
        <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-4">
          <Clock className="w-5 h-5 text-emerald-400" />
          Personal en Turno (Actualmente Activos)
        </h3>
        
        {activos.length === 0 ? (
          <div className="text-center py-6 text-slate-400 bg-slate-900 rounded-lg">
            No hay ningún empleado trabajando en este momento.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {activos.map(turno => (
              <div key={turno.id} className="bg-slate-900 border border-slate-700 rounded-lg p-4 flex flex-col gap-2 relative">
                <span className="absolute top-4 right-4 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
                <span className="font-bold text-slate-200 text-lg">{turno.nombre_usuario}</span>
                <span className="text-xs font-semibold text-slate-400 bg-slate-800 px-2 py-1 rounded w-max uppercase">
                  {turno.rol}
                </span>
                <div className="text-sm text-slate-300 mt-2">
                  <span className="text-slate-500 block">Entrada:</span>
                  {formatearFechaHora(turno.entrada_en)}
                </div>
                <div className="text-sm text-emerald-400 font-semibold mt-1">
                  Tiempo: {calcularDuracion(turno.entrada_en, null)}
                </div>
                <button
                  onClick={() => handleCerrarTurno(turno.id)}
                  className="mt-3 w-full text-xs font-bold text-red-400 hover:text-white bg-slate-800 hover:bg-red-900 border border-slate-700 hover:border-red-500 transition py-1.5 rounded"
                >
                  Forzar Cierre
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
        <div className="p-5 border-b border-slate-700 flex justify-between items-center bg-slate-800">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-blue-400" />
            Historial de Jornadas
          </h3>
          <button onClick={cargarDatos} className="text-slate-400 hover:text-white">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-900/50 text-slate-400 uppercase text-xs font-semibold">
              <tr>
                <th className="px-4 py-3">Empleado</th>
                <th className="px-4 py-3">Rol</th>
                <th className="px-4 py-3">Entrada</th>
                <th className="px-4 py-3">Salida</th>
                <th className="px-4 py-3 text-right">Duración</th>
                <th className="px-4 py-3">Cierre</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {historial.map((turno) => (
                <tr key={turno.id} className="hover:bg-slate-700/30">
                  <td className="px-4 py-3 font-medium text-slate-200">{turno.nombre_usuario}</td>
                  <td className="px-4 py-3">
                    <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-700">
                      {turno.rol}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {formatearFechaHora(turno.entrada_en)}
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {turno.salida_en ? formatearFechaHora(turno.salida_en) : (
                      <span className="text-emerald-400 text-xs font-semibold flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                        ACTIVO
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right font-semibold text-slate-300">
                    {calcularDuracion(turno.entrada_en, turno.salida_en)}
                  </td>
                  <td className="px-4 py-3">
                    {turno.motivo_cierre === 'MANUAL' && (
                      <span className="text-blue-400 flex items-center gap-1 text-xs"><CheckCircle2 className="w-3 h-3"/> Empleado</span>
                    )}
                    {turno.motivo_cierre === 'CIERRE_CAJA' && (
                      <span className="text-purple-400 flex items-center gap-1 text-xs"><LogOut className="w-3 h-3"/> Por Caja</span>
                    )}
                    {turno.motivo_cierre === 'ADMIN' && (
                      <span className="text-orange-400 flex items-center gap-1 text-xs"><AlertCircle className="w-3 h-3"/> Admin</span>
                    )}
                    {!turno.motivo_cierre && (
                      <span className="text-slate-500">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
