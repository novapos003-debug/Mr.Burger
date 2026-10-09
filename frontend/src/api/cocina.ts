import api from './client'
import type { Ticket } from '../types/cocina'

export const getColaCocina = async (): Promise<Ticket[]> => {
  const res = await api.get<Ticket[]>('/cocina/cola')
  return res.data
}

export const aceptarDetalle = async (detalleId: number): Promise<Ticket> => {
  const res = await api.post<Ticket>(`/cocina/detalles/${detalleId}/aceptar`)
  return res.data
}

export const marcarListo = async (detalleId: number): Promise<Ticket> => {
  const res = await api.post<Ticket>(`/cocina/detalles/${detalleId}/listo`)
  return res.data
}

export const cancelarDetalle = async (detalleId: number): Promise<void> => {
  await api.post(`/cocina/detalles/${detalleId}/cancelar`)
}

/**
 * Acepta todos los detalles en estado ENVIADO del ticket (descuenta inventario en backend)
 */
export const aceptarTicket = async (ticket: Ticket): Promise<void> => {
  const pendientes: number[] = []
  for (const ronda of ticket.rondas) {
    for (const d of ronda.detalles) {
      if (d.estado === 'ENVIADO') {
        pendientes.push(d.detalle_id)
      }
    }
  }
  for (const id of pendientes) {
    await aceptarDetalle(id)
  }
}

/**
 * Marca como LISTO todos los detalles en estado PREPARANDO del ticket
 */
export const marcarTicketListo = async (ticket: Ticket): Promise<void> => {
  const preparando: number[] = []
  for (const ronda of ticket.rondas) {
    for (const d of ronda.detalles) {
      if (d.estado === 'PREPARANDO') {
        preparando.push(d.detalle_id)
      }
    }
  }
  for (const id of preparando) {
    await marcarListo(id)
  }
}
