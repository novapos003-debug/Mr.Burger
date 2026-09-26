import { useEffect, useRef, useState, useCallback } from 'react'
import type { WebSocketStatus, WebSocketEvent } from '../types/cocina'
import { getWsBaseUrl } from '../api/client'

interface UseCocinaWebSocketOptions {
  onNewOrder?: (event: WebSocketEvent) => void
  onOrderUpdate?: (event: WebSocketEvent) => void
}

export function useCocinaWebSocket({ onNewOrder, onOrderUpdate }: UseCocinaWebSocketOptions = {}) {
  const [status, setStatus] = useState<WebSocketStatus>('desconectado')
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const unmountedRef = useRef(false)

  // Callbacks refs to avoid stale closures in event listeners
  const onNewOrderRef = useRef(onNewOrder)
  const onOrderUpdateRef = useRef(onOrderUpdate)

  useEffect(() => {
    onNewOrderRef.current = onNewOrder
    onOrderUpdateRef.current = onOrderUpdate
  }, [onNewOrder, onOrderUpdate])

  const connect = useCallback(() => {
    if (unmountedRef.current) return

    const token = localStorage.getItem('pos_token')
    if (!token) {
      setStatus('desconectado')
      return
    }

    // Cerrar conexión anterior si existía
    if (wsRef.current) {
      try {
        wsRef.current.close()
      } catch {
        // ignore
      }
    }

    setStatus('reconectando')
    const baseWs = getWsBaseUrl()
    const separator = baseWs.includes('?') ? '&' : '?'
    const wsUrl = `${baseWs}${separator}token=${encodeURIComponent(token)}`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        if (unmountedRef.current) return
        setStatus('conectado')
      }

      ws.onmessage = (event) => {
        if (unmountedRef.current) return
        try {
          const payload: WebSocketEvent = JSON.parse(event.data)

          // Eventos de nuevos pedidos o rondas que entran a cocina
          if (payload.evento === 'pedido_enviado' || payload.evento === 'ronda_agregada') {
            onNewOrderRef.current?.(payload)
          } else {
            // Actualizaciones de estado (detalle_aceptado, detalle_listo, etc.)
            onOrderUpdateRef.current?.(payload)
          }
        } catch (err) {
          console.error('Error parseando mensaje WebSocket:', err)
        }
      }

      ws.onclose = (e) => {
        if (unmountedRef.current) return
        // Si el código es 1008 (autenticación fallida), no reintentar en bucle rápido
        if (e.code === 1008) {
          setStatus('desconectado')
          return
        }

        setStatus('reconectando')
        if (reconnectTimeoutRef.current) {
          window.clearTimeout(reconnectTimeoutRef.current)
        }
        reconnectTimeoutRef.current = window.setTimeout(() => {
          connect()
        }, 3000)
      }

      ws.onerror = () => {
        if (unmountedRef.current) return
        try {
          ws.close()
        } catch {
          // ignore
        }
      }
    } catch (err) {
      console.error('Error iniciando WebSocket:', err)
      setStatus('reconectando')
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect()
      }, 3000)
    }
  }, [])

  useEffect(() => {
    unmountedRef.current = false
    connect()

    return () => {
      unmountedRef.current = true
      if (reconnectTimeoutRef.current) {
        window.clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        try {
          wsRef.current.close()
        } catch {
          // ignore
        }
      }
    }
  }, [connect])

  const reconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      window.clearTimeout(reconnectTimeoutRef.current)
    }
    connect()
  }, [connect])

  return {
    status,
    reconnect,
  }
}
