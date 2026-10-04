import React, { useState, useEffect } from 'react'
import { Sparkles, RefreshCw, X } from 'lucide-react'

export const UpdateBanner: React.FC = () => {
  const [hasUpdate, setHasUpdate] = useState(false)
  const [updating, setUpdating] = useState(false)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    if (!('serviceWorker' in navigator)) return

    let registration: ServiceWorkerRegistration | null = null

    navigator.serviceWorker.ready.then((reg) => {
      registration = reg

      // Forzar chequeo de actualización inmediato al abrir la aplicación
      reg.update().catch(() => {})

      // Escuchar si ya hay un worker esperando
      if (reg.waiting) {
        setHasUpdate(true)
      }

      // Escuchar si se encuentra una nueva versión
      reg.addEventListener('updatefound', () => {
        const newWorker = reg.installing
        if (!newWorker) return

        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            setHasUpdate(true)
          }
        })
      })
    })

    // Escuchar cuando el nuevo Service Worker toma el control
    let refreshing = false
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (!refreshing) {
        refreshing = true
        window.location.reload()
      }
    })

    // Chequear periódicamente cada 5 minutos por si hay nueva versión en el servidor
    const checkInterval = setInterval(() => {
      if (registration && navigator.onLine) {
        registration.update().catch(() => {})
      }
    }, 5 * 60 * 1000)

    // Chequear al reanudar la ventana / app en Android
    const onVisibilityChange = () => {
      if (document.visibilityState === 'visible' && registration && navigator.onLine) {
        registration.update().catch(() => {})
      }
    }
    document.addEventListener('visibilitychange', onVisibilityChange)

    return () => {
      clearInterval(checkInterval)
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }
  }, [])

  const handleUpdate = () => {
    setUpdating(true)
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then((reg) => {
        if (reg.waiting) {
          reg.waiting.postMessage({ type: 'SKIP_WAITING' })
        }
      })
    }
    // Si no cambió en 1.5s, forzar recarga
    setTimeout(() => {
      window.location.reload()
    }, 1500)
  }

  if (!hasUpdate || dismissed) return null

  return (
    <div className="fixed bottom-4 right-4 left-4 sm:left-auto sm:w-96 z-50 bg-gradient-to-r from-orange-600 to-amber-600 text-white p-3.5 rounded-2xl shadow-2xl border border-orange-400/40 flex items-center justify-between gap-3 animate-slide-up">
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-xl bg-white/20 flex items-center justify-center shrink-0">
          <Sparkles className="w-4 h-4 text-white animate-spin" />
        </div>
        <div>
          <p className="text-xs font-bold leading-tight">¡Nueva versión disponible!</p>
          <p className="text-[10px] text-white/80">Actualización del sistema descargada y lista.</p>
        </div>
      </div>

      <div className="flex items-center gap-1.5 shrink-0">
        <button
          onClick={handleUpdate}
          disabled={updating}
          className="px-3 py-1.5 bg-white text-orange-700 hover:bg-orange-50 font-bold text-xs rounded-xl shadow cursor-pointer transition flex items-center gap-1.5 active:scale-95 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${updating ? 'animate-spin' : ''}`} />
          <span>{updating ? 'Actualizando...' : 'Actualizar'}</span>
        </button>
        <button
          onClick={() => setDismissed(true)}
          className="p-1 text-white/70 hover:text-white rounded-lg transition"
          title="Descartar"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
