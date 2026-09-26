import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'

export interface SyncStatus {
  online: boolean
  sincronizando: boolean
  pendientes: number
  aplicadas: number
  conflictos: number
  ultimaSync: string | null
  cerebroModo: string
  sucursalId: string
  ultimoError: string | null
  lanError: boolean
  cargando: boolean
}

export function useSyncStatus(intervalMs = 6000) {
  const [status, setStatus] = useState<SyncStatus>({
    online: true,
    sincronizando: false,
    pendientes: 0,
    aplicadas: 0,
    conflictos: 0,
    ultimaSync: null,
    cerebroModo: 'LOCAL',
    sucursalId: 'SUC-01',
    ultimoError: null,
    lanError: false,
    cargando: true,
  })

  const consultarEstado = useCallback(async () => {
    try {
      const resp = await api.get('/sync/estado', { timeout: 3500 })
      const data = resp.data
      setStatus({
        online: data.online ?? true,
        sincronizando: data.sincronizando ?? false,
        pendientes: data.pendientes ?? 0,
        aplicadas: data.aplicadas ?? 0,
        conflictos: data.conflictos ?? 0,
        ultimaSync: data.ultima_sincronizacion ?? null,
        cerebroModo: data.cerebro_modo ?? 'LOCAL',
        sucursalId: data.sucursal_id ?? 'SUC-01',
        ultimoError: data.ultimo_error ?? null,
        lanError: false,
        cargando: false,
      })
    } catch (err: any) {
      // Si la petición a /sync/estado falla por timeout o error de red hacia el backend local
      setStatus((prev) => ({
        ...prev,
        lanError: !err.response, // true si es fallo de red (servidor local caído o sin wifi)
        ultimoError: err.message || 'Error de conexión LAN',
        cargando: false,
      }))
    }
  }, [])

  const forzarSync = useCallback(async () => {
    try {
      setStatus((prev) => ({ ...prev, sincronizando: true }))
      await api.post('/sync/forzar')
      await consultarEstado()
    } catch (err: any) {
      console.warn('Error al forzar sincronización:', err)
      await consultarEstado()
    }
  }, [consultarEstado])

  useEffect(() => {
    consultarEstado()
    const timer = setInterval(consultarEstado, intervalMs)
    return () => clearInterval(timer)
  }, [consultarEstado, intervalMs])

  return { ...status, forzarSync, refrescar: consultarEstado }
}
