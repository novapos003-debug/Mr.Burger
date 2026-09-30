import api from './client'
import type { TurnoLaboral } from '../types/asistencia'

export const registrarEntradaApi = async (): Promise<TurnoLaboral> => {
  const { data } = await api.post<TurnoLaboral>('/asistencia/entrada')
  return data
}

export const registrarSalidaApi = async (): Promise<TurnoLaboral> => {
  const { data } = await api.post<TurnoLaboral>('/asistencia/salida')
  return data
}

export const obtenerMiTurnoApi = async (): Promise<TurnoLaboral | null> => {
  const { data } = await api.get<TurnoLaboral | null>('/asistencia/mi-turno')
  return data
}

export const getTurnosActivosApi = async (): Promise<TurnoLaboral[]> => {
  const { data } = await api.get<TurnoLaboral[]>('/asistencia/admin/activos')
  return data
}

export const getTurnosHistorialApi = async (): Promise<TurnoLaboral[]> => {
  const { data } = await api.get<TurnoLaboral[]>('/asistencia/admin/historial')
  return data
}

export const cerrarTurnoAdminApi = async (turnoId: number): Promise<TurnoLaboral> => {
  const { data } = await api.post<TurnoLaboral>(`/asistencia/admin/${turnoId}/cerrar`)
  return data
}
