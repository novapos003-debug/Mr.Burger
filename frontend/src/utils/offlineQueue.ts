import {
  crearPedidoApi,
  enviarCocinaApi,
  agregarRondaApi,
  type CrearPedidoPayload,
  type AgregarRondaPayload,
} from '../api/mesero'

export interface PendingOrder {
  id: string // UUID local
  tipo: 'NUEVO_PEDIDO' | 'RONDA'
  pedidoId?: number
  mesaNumero?: number
  payloadNuevo?: CrearPedidoPayload
  payloadRonda?: AgregarRondaPayload
  timestamp: number
  reintentos: number
}

const STORAGE_KEY = 'pos_mesero_offline_queue'

export const getPendingOrders = (): PendingOrder[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export const savePendingOrder = (order: Omit<PendingOrder, 'id' | 'timestamp' | 'reintentos'>): PendingOrder => {
  const queue = getPendingOrders()
  const newOrder: PendingOrder = {
    ...order,
    id: `offline-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
    timestamp: Date.now(),
    reintentos: 0,
  }
  queue.push(newOrder)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(queue))
  return newOrder
}

export const removePendingOrder = (id: string): void => {
  const queue = getPendingOrders().filter((o) => o.id !== id)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(queue))
}

/**
 * Intenta procesar todos los pedidos en cola acumulados durante caídas temporales de Wi-Fi
 */
export const syncPendingOrders = async (
  onSuccessOrder?: (order: PendingOrder, detalle: string) => void
): Promise<{ exitosos: number; pendientes: number }> => {
  const queue = getPendingOrders()
  if (queue.length === 0) return { exitosos: 0, pendientes: 0 }

  let exitosos = 0
  const remaining: PendingOrder[] = []

  for (const order of queue) {
    try {
      if (order.tipo === 'NUEVO_PEDIDO' && order.payloadNuevo) {
        order.payloadNuevo.idempotency_key = order.id
        const nuevo = await crearPedidoApi(order.payloadNuevo)
        await enviarCocinaApi(nuevo.id)
        exitosos++
        onSuccessOrder?.(order, `Comanda de Mesa #${order.mesaNumero || ''} enviada a cocina`)
      } else if (order.tipo === 'RONDA' && order.pedidoId && order.payloadRonda) {
        await agregarRondaApi(order.pedidoId, order.payloadRonda)
        exitosos++
        onSuccessOrder?.(order, `Ronda #${order.payloadRonda.ronda} de Mesa #${order.mesaNumero || ''} enviada a cocina`)
      }
    } catch (err: any) {
      // Si fue error de conexión, se mantiene en la cola para el próximo ciclo
      if (!err.response || err.code === 'ERR_NETWORK') {
        remaining.push({ ...order, reintentos: order.reintentos + 1 })
      } else {
        // Si fue error 4xx de validación, registrarlo y descartar para no bloquear la cola
        console.error('Error permanente al procesar pedido offline:', err)
      }
    }
  }

  localStorage.setItem(STORAGE_KEY, JSON.stringify(remaining))
  return { exitosos, pendientes: remaining.length }
}
