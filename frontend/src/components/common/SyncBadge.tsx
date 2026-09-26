import React, { useState } from 'react'
import {
  Cloud,
  CloudOff,
  RefreshCw,
  WifiOff,
  Server,
  X,
} from 'lucide-react'
import { useSyncStatus } from '../../hooks/useSyncStatus'

export const SyncBadge: React.FC = () => {
  const {
    online,
    sincronizando,
    pendientes,
    aplicadas,
    conflictos,
    ultimaSync,
    cerebroModo,
    sucursalId,
    ultimoError,
    lanError,
    forzarSync,
    refrescar,
  } = useSyncStatus(5000)

  const [modalAbierto, setModalAbierto] = useState(false)
  const [ejecutandoForzado, setEjecutandoForzado] = useState(false)

  const handleForzar = async () => {
    setEjecutandoForzado(true)
    await forzarSync()
    setEjecutandoForzado(false)
  }

  // 1. Fallo crítico de conexión LAN (la tablet o PC no alcanza el servidor de la caja)
  if (lanError) {
    return (
      <button
        onClick={() => setModalAbierto(true)}
        className="inline-flex items-center gap-1.5 text-[11px] font-bold text-red-300 bg-red-950/80 border border-red-700/80 px-2 py-0.5 rounded shadow-sm hover:bg-red-900 transition cursor-pointer animate-pulse"
        title="Sin conexión al servidor local de la caja"
      >
        <WifiOff className="w-3.5 h-3.5" />
        <span>SIN RED CAJA</span>
      </button>
    )
  }

  // 2. Sincronizando activamente con la nube
  if (sincronizando || ejecutandoForzado) {
    return (
      <button
        onClick={() => setModalAbierto(true)}
        className="inline-flex items-center gap-1.5 text-[11px] font-bold text-sky-300 bg-sky-950/80 border border-sky-700/80 px-2 py-0.5 rounded shadow-sm hover:bg-sky-900 transition cursor-pointer"
        title="Transmitiendo datos a la nube en segundo plano"
      >
        <RefreshCw className="w-3.5 h-3.5 animate-spin text-sky-400" />
        <span>SINCRONIZANDO ({pendientes})</span>
      </button>
    )
  }

  // 3. Modo Local con registros pendientes (o sin internet externo hacia la nube)
  if (pendientes > 0 || !online) {
    return (
      <>
        <button
          onClick={() => setModalAbierto(true)}
          className="inline-flex items-center gap-1.5 text-[11px] font-bold text-amber-300 bg-amber-950/80 border border-amber-600/80 px-2 py-0.5 rounded shadow-sm hover:bg-amber-900 transition cursor-pointer"
          title={`Operando localmente. ${pendientes} operaciones pendientes de subir a la nube.`}
        >
          <CloudOff className="w-3.5 h-3.5 text-amber-400" />
          <span>MODO LOCAL ({pendientes})</span>
        </button>

        {modalAbierto && renderModal()}
      </>
    )
  }

  // 4. Todo en línea y sincronizado al día
  return (
    <>
      <button
        onClick={() => setModalAbierto(true)}
        className="inline-flex items-center gap-1.5 text-[11px] font-bold text-emerald-300 bg-emerald-950/80 border border-emerald-600/80 px-2 py-0.5 rounded shadow-sm hover:bg-emerald-900 transition cursor-pointer"
        title="Conectado a la nube. Todo sincronizado al día."
      >
        <Cloud className="w-3.5 h-3.5 text-emerald-400" />
        <span>EN LÍNEA</span>
      </button>

      {modalAbierto && renderModal()}
    </>
  )

  function renderModal() {
    return (
      <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
        <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl max-w-md w-full p-5 text-left text-white animate-in fade-in duration-150">
          {/* Header */}
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Server className="w-5 h-5 text-orange-500" />
              <div>
                <h3 className="font-bold text-sm text-slate-100">Estado de Sincronización y Red</h3>
                <p className="text-[11px] text-slate-400">Servidor Local ({sucursalId}) &bull; Modo: {cerebroModo}</p>
              </div>
            </div>
            <button
              onClick={() => setModalAbierto(false)}
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Estado general */}
          <div className="mt-4 p-3 rounded-lg bg-slate-950/80 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Conexión con la Nube:</span>
              <span
                className={`font-semibold px-2 py-0.5 rounded ${
                  online
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    : 'bg-amber-950 text-amber-300 border border-amber-800'
                }`}
              >
                {online ? '🟢 Conectado' : '🟠 Sin Internet Externo (Modo Local 100% Operativo)'}
              </span>
            </div>

            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Servidor en Caja (LAN):</span>
              <span className="font-semibold text-emerald-400">
                {lanError ? '🔴 Desconectado' : '✅ En Vivo (Operación Normal)'}
              </span>
            </div>

            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Última Sincronización:</span>
              <span className="text-slate-200 font-mono text-[11px]">
                {ultimaSync ? new Date(ultimaSync).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : 'Pendiente'}
              </span>
            </div>

            {ultimoError && (
              <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-800/80">
                <span className="text-slate-400">Detalle Red:</span>
                <span className="text-amber-400 text-[11px] font-mono truncate max-w-[220px]" title={ultimoError}>
                  {ultimoError}
                </span>
              </div>
            )}
          </div>

          {/* Métricas de Cola Outbox */}
          <div className="grid grid-cols-3 gap-2.5 mt-3">
            <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 text-center">
              <span className="text-[11px] text-slate-400 block font-medium">Pendientes</span>
              <span className="text-lg font-bold text-amber-400">{pendientes}</span>
            </div>
            <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 text-center">
              <span className="text-[11px] text-slate-400 block font-medium">Sincronizadas</span>
              <span className="text-lg font-bold text-emerald-400">{aplicadas}</span>
            </div>
            <div className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 text-center">
              <span className="text-[11px] text-slate-400 block font-medium">Conflictos</span>
              <span className="text-lg font-bold text-slate-400">{conflictos}</span>
            </div>
          </div>

          {/* Nota operativa */}
          <div className="mt-3 text-[11px] text-slate-400 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/50">
            <p className="flex items-start gap-1.5">
              <span className="text-orange-400 font-bold">&bull;</span>
              <span>
                <strong>Operación sin Internet:</strong> Si la nube no está disponible, todas las ventas, cobros y descuentos de inventario se guardan en el servidor local de la caja y se enviarán automáticamente en cuanto se restablezca la conexión.
              </span>
            </p>
          </div>

          {/* Footer Actions */}
          <div className="mt-4 flex items-center justify-between pt-3 border-t border-slate-800">
            <button
              onClick={() => refrescar()}
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition cursor-pointer"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Actualizar estado</span>
            </button>

            <button
              onClick={handleForzar}
              disabled={ejecutandoForzado || sincronizando}
              className="px-3.5 py-1.5 rounded-lg bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer shadow-md shadow-orange-600/20"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${ejecutandoForzado ? 'animate-spin' : ''}`} />
              <span>Sincronizar Ahora</span>
            </button>
          </div>
        </div>
      </div>
    )
  }
}
