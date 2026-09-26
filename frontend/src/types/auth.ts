export type UserRole = 'admin' | 'cajero' | 'mesero' | 'cocina'

export interface Usuario {
  id: number
  rol_id: number
  rol: UserRole
  nombre: string
  usuario: string
  activo: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
  rol: UserRole
  nombre: string
}
