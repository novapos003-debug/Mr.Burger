export interface TurnoLaboral {
  id: number;
  usuario_id: number;
  nombre_usuario: string;
  rol: string;
  entrada_en: string;
  salida_en: string | null;
  motivo_cierre: string | null;
}
