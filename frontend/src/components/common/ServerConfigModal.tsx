import React, { useState } from 'react'
import { Server, CheckCircle2, AlertCircle, X, Wifi } from 'lucide-react'
import { getServerIp, setServerIp } from '../../api/client'
import { checkHealthApi } from '../../api/auth'

interface ServerConfigModalProps {
  isOpen: boolean
  onClose: () => void
  onSave?: () => void
}

export const ServerConfigModal: React.FC<ServerConfigModalProps> = ({
  isOpen,
  onClose,
  onSave,
}) => {
  const [ip, setIp] = useState(getServerIp())
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{
    ok: boolean
    mensaje: string
  } | null>(null)

  if (!isOpen) return null

  const handleTestConnection = async () => {
    setTesting(true)
    setTestResult(null)
    setServerIp(ip)

    try {
      const ok = await checkHealthApi()
      if (ok) {
        setTestResult({
          ok: true,
          mensaje: '¡Conexión exitosa con el servidor local del restaurante!',
        })
      } else {
        setTestResult({
          ok: false,
          mensaje: 'El servidor no respondió. Verifica la IP y que esté en el mismo Wi-Fi.',
        })
      }
    } catch {
      setTestResult({
        ok: false,
        mensaje: 'No se pudo conectar al servidor. Revisa que el puerto 8000 esté accesible.',
      })
    } finally {
      setTesting(false)
    }
  }

  const handleSave = () => {
    setServerIp(ip)
    onSave?.()
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-sm w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-orange-600/20 text-orange-400 flex items-center justify-center">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Configurar Servidor Local</h3>
              <p className="text-[11px] text-slate-400">IP del cerebro LAN en el restaurante</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-slate-300 p-1 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold text-slate-300">
            Dirección IP del Servidor LAN
          </label>
          <div className="relative">
            <input
              type="text"
              value={ip}
              onChange={(e) => {
                setIp(e.target.value)
                setTestResult(null)
              }}
              placeholder="ej. 192.168.1.50:8000"
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-600 focus:outline-none focus:border-orange-500"
            />
          </div>
          <p className="text-[10px] text-slate-500">
            Deja en blanco si accedes directamente desde el navegador en la misma máquina o proxy Vite.
          </p>
        </div>

        {testResult && (
          <div
            className={`p-3 rounded-xl border text-xs flex items-start gap-2 ${
              testResult.ok
                ? 'bg-emerald-950/70 border-emerald-800 text-emerald-200'
                : 'bg-red-950/70 border-red-800 text-red-200'
            }`}
          >
            {testResult.ok ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            )}
            <span>{testResult.mensaje}</span>
          </div>
        )}

        <div className="flex gap-2 pt-2">
          <button
            type="button"
            onClick={handleTestConnection}
            disabled={testing}
            className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <Wifi className="w-3.5 h-3.5" />
            <span>{testing ? 'Probando...' : 'Probar'}</span>
          </button>

          <button
            type="button"
            onClick={handleSave}
            className="flex-1 py-2 bg-orange-600 hover:bg-orange-500 text-white text-xs font-bold rounded-xl transition cursor-pointer"
          >
            Guardar
          </button>
        </div>
      </div>
    </div>
  )
}
