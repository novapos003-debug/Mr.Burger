import React, { useState, useEffect } from 'react'
import type { MovimientoCajaOut, MovimientoCajaIn, TipoMovimiento, CategoriaMovimiento } from '../../types/caja'
import { getMovimientos, crearMovimiento } from '../../api/caja'
import {
  FileSpreadsheet,
  X,
  Plus,
  ArrowUpRight,
  ArrowDownLeft,
  Printer,
  Loader2,
  Calendar,
  AlertCircle,
  FileText,
} from 'lucide-react'
import { TirillaModal } from '../common/TirillaModal'

interface Props {
  isOpen: boolean
  onClose: () => void
}

export const MovimientosModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const [movimientos, setMovimientos] = useState<MovimientoCajaOut[]>([])
  const [loading, setLoading] = useState(false)
  const [vista, setVista] = useState<'LISTA' | 'NUEVO' | 'VOUCHER'>('LISTA')
  const [selectedMov, setSelectedMov] = useState<MovimientoCajaOut | null>(null)
  const [isTirillaOpen, setIsTirillaOpen] = useState(false)

  // Formulario nuevo movimiento
  const [tipo, setTipo] = useState<TipoMovimiento>('SALIDA')
  const [categoria, setCategoria] = useState<CategoriaMovimiento>('PROVEEDOR')
  const [concepto, setConcepto] = useState<string>('')
  const [descripcion, setDescripcion] = useState<string>('')
  const [valor, setValor] = useState<number>(0)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchMovs = async () => {
    try {
      setLoading(true)
      const data = await getMovimientos()
      setMovimientos(data)
    } catch (err: any) {
      console.error('Error cargando movimientos:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      fetchMovs()
      setVista('LISTA')
      setError(null)
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleCrear = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!valor || valor <= 0) {
      setError('El valor debe ser mayor a 0')
      return
    }
    if (!descripcion.trim() || descripcion.trim().length < 3) {
      setError('La descripción explicativa es obligatoria (mínimo 3 caracteres)')
      return
    }

    try {
      setGuardando(true)
      setError(null)
      const data: MovimientoCajaIn = {
        tipo,
        categoria,
        concepto: concepto.trim() || undefined,
        descripcion: descripcion.trim(),
        valor: Number(valor),
      }
      const nuevo = await crearMovimiento(data)
      setSelectedMov(nuevo)
      setVista('VOUCHER')
      fetchMovs()
    } catch (err: any) {
      console.error('Error creando movimiento:', err)
      setError(
        err.response?.status === 403
          ? 'Solo un Administrador o Supervisor tiene autorización para registrar retiros/depósitos manuales de caja menor'
          : err.response?.data?.detail || 'Error al registrar movimiento'
      )
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-3 sm:p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Cabecera */}
        <div className="p-4 border-b border-slate-800 bg-slate-800/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-600/30 border border-sky-500/40 flex items-center justify-center text-sky-400">
              <FileSpreadsheet className="w-6 h-6" />
            </div>
            <div>
              <h2 className="font-black text-white text-lg tracking-wide">
                Gastos Operativos & Caja Menor
              </h2>
              <p className="text-xs text-slate-400">
                Registro de gastos (Axion, esponjas, papel) y comprobantes de caja
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Barra de Pestañas / Acciones */}
        <div className="px-4 py-2 bg-slate-950/60 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setVista('LISTA')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
                vista === 'LISTA'
                  ? 'bg-sky-600 text-white shadow'
                  : 'bg-slate-800/60 text-slate-400 hover:text-white'
              }`}
            >
              Historial de Gastos y Vales
            </button>
            <button
              onClick={() => {
                setVista('NUEVO')
                setError(null)
              }}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
                vista === 'NUEVO'
                  ? 'bg-amber-500 text-slate-950 shadow'
                  : 'bg-slate-800/60 text-slate-400 hover:text-white'
              }`}
            >
              <Plus className="w-3.5 h-3.5" />
              <span>💸 Registrar Gasto / Salida</span>
            </button>
          </div>
        </div>

        {/* Cuerpo */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1">
          {error && (
            <div className="p-3 bg-rose-950/80 border border-rose-800 text-rose-300 rounded-xl text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {vista === 'LISTA' && (
            <>
              {loading ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 text-sky-400 animate-spin mb-2" />
                  <span className="text-xs text-slate-400 font-semibold">Cargando movimientos...</span>
                </div>
              ) : movimientos.length === 0 ? (
                <div className="text-center py-12 text-slate-500 text-xs">
                  No hay movimientos manuales de caja menor registrados en el turno.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {movimientos.map((m) => {
                    const isEntrada = m.tipo === 'ENTRADA'
                    return (
                      <div
                        key={m.id}
                        className="bg-slate-950 p-3.5 rounded-2xl border border-slate-800 hover:border-slate-700 transition flex items-center justify-between gap-3"
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold ${
                              isEntrada
                                ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60'
                                : 'bg-rose-950/80 text-rose-400 border border-rose-800/60'
                            }`}
                          >
                            {isEntrada ? (
                              <ArrowDownLeft className="w-5 h-5" />
                            ) : (
                              <ArrowUpRight className="w-5 h-5" />
                            )}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-white text-sm">
                                {m.concepto || m.categoria}
                              </span>
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                                Folio #{m.id}
                              </span>
                            </div>
                            <p className="text-xs text-slate-400 mt-0.5">{m.descripcion}</p>
                            <span className="text-[10px] text-slate-500 flex items-center gap-1 mt-1">
                              <Calendar className="w-3 h-3" />
                              {new Date(m.creado_en).toLocaleString('es-CO')}
                            </span>
                          </div>
                        </div>

                        <div className="flex flex-col items-end gap-1.5 shrink-0">
                          <span
                            className={`font-mono font-black text-base ${
                              isEntrada ? 'text-emerald-400' : 'text-rose-400'
                            }`}
                          >
                            {isEntrada ? '+' : '-'}${Number(m.valor).toLocaleString('es-CO')}
                          </span>
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedMov(m)
                              setVista('VOUCHER')
                            }}
                            className="flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
                          >
                            <FileText className="w-3 h-3 text-sky-400" />
                            <span>Ver Vale</span>
                          </button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </>
          )}

          {vista === 'NUEVO' && (
            <form onSubmit={handleCrear} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setTipo('SALIDA')}
                  className={`py-2.5 px-3 rounded-xl font-bold text-xs border transition cursor-pointer flex items-center justify-center gap-1.5 ${
                    tipo === 'SALIDA'
                      ? 'bg-rose-950 border-rose-500 text-rose-300 shadow'
                      : 'bg-slate-950 border-slate-800 text-slate-400'
                  }`}
                >
                  <ArrowUpRight className="w-4 h-4" />
                  <span>RETIRO / SALIDA DE EFECTIVO</span>
                </button>
                <button
                  type="button"
                  onClick={() => setTipo('ENTRADA')}
                  className={`py-2.5 px-3 rounded-xl font-bold text-xs border transition cursor-pointer flex items-center justify-center gap-1.5 ${
                    tipo === 'ENTRADA'
                      ? 'bg-emerald-950 border-emerald-500 text-emerald-300 shadow'
                      : 'bg-slate-950 border-slate-800 text-slate-400'
                  }`}
                >
                  <ArrowDownLeft className="w-4 h-4" />
                  <span>DEPÓSITO / ENTRADA DE EFECTIVO</span>
                </button>
              </div>

              {/* Atajos Rápidos de Gastos Operativos Comunes */}
              <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-2xl space-y-1.5">
                <span className="text-[11px] font-bold text-slate-400 block">
                  ⚡ Atajos rápidos de Gastos Operativos comunes (un clic para rellenar concepto y descripción):
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {[
                    { label: '🧼 Jabón Axion', concepto: 'Aseo - Axion', desc: 'Jabón Axion para lavado de loza' },
                    { label: '🧽 Esponjas', concepto: 'Aseo - Esponjas', desc: 'Esponjas y fibra para cocina' },
                    { label: '🧻 Papel Higiénico', concepto: 'Aseo - Papel Baño', desc: 'Papel higiénico para baños' },
                    { label: '🧻 Papel Cocina', concepto: 'Cocina - Papel Toalla', desc: 'Papel toalla absorbente para cocina' },
                    { label: '🧴 Límpido / Cloro', concepto: 'Aseo - Límpido', desc: 'Límpido y desinfectante para pisos' },
                    { label: '🧾 Rollos Facturación', concepto: 'Insumos - Papel Térmico', desc: 'Rollos de papel térmico para impresoras POS' },
                    { label: '🥡 Bolsas Extra', concepto: 'Empaques - Bolsas', desc: 'Bolsas plásticas extras para despachos' },
                  ].map((chip) => (
                    <button
                      key={chip.label}
                      type="button"
                      onClick={() => {
                        setTipo('SALIDA')
                        setCategoria('GASTO_OPERATIVO')
                        setConcepto(chip.concepto)
                        setDescripcion(chip.desc)
                      }}
                      className="px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-900 hover:bg-slate-800 text-rose-300 border border-slate-800 hover:border-rose-600/60 transition cursor-pointer active:scale-95"
                    >
                      {chip.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    Categoría
                  </label>
                  <select
                    value={categoria}
                    onChange={(e) => setCategoria(e.target.value as CategoriaMovimiento)}
                    className="w-full py-2.5 px-3 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs font-semibold focus:outline-none"
                  >
                    <option value="GASTO_OPERATIVO">GASTO OPERATIVO (Axion, esponjas, papel higiénico, cocina...)</option>
                    <option value="PROVEEDOR">PROVEEDOR (Compras pan, verduras, insumos)</option>
                    <option value="ADELANTO">ADELANTO (Anticipo de sueldo)</option>
                    <option value="PAGO_TURNO">PAGO TURNO (Domiciliario / Empleado)</option>
                    <option value="PRESTAMO">PRÉSTAMO</option>
                    <option value="CAMBIO_INICIAL">CAMBIO INICIAL (Inyección de sencillo)</option>
                    <option value="OTRO">OTRO CONCEPTO</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    Concepto / Beneficiario
                  </label>
                  <input
                    type="text"
                    value={concepto}
                    onChange={(e) => setConcepto(e.target.value)}
                    className="w-full py-2.5 px-3 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs focus:outline-none"
                    placeholder="Ej: Aseo Axion, D1, Supermercado, etc."
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">
                  Importe Numérico ($ COP) <span className="text-rose-400">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 font-bold">$</span>
                  <input
                    type="number"
                    min="100"
                    step="500"
                    value={valor || ''}
                    onChange={(e) => setValor(Number(e.target.value))}
                    className="w-full pl-8 pr-4 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-amber-400 font-mono font-bold text-xl focus:outline-none focus:border-amber-500"
                    placeholder="0"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1">
                  Descripción / Referencia de Justificación <span className="text-rose-400">*</span>
                </label>
                <textarea
                  rows={2}
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                  className="w-full p-2.5 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
                  placeholder="Ej: Pago de 10 paquetes de pan hamburguesa Bimbo con factura #8942"
                  required
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setVista('LISTA')}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white transition cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={guardando}
                  className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl font-black text-xs bg-sky-600 hover:bg-sky-500 text-white shadow-lg transition active:scale-95 disabled:opacity-50 cursor-pointer"
                >
                  {guardando ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Plus className="w-4 h-4" />
                  )}
                  <span>Registrar e Imprimir Vale</span>
                </button>
              </div>
            </form>
          )}

          {vista === 'VOUCHER' && selectedMov && (
            <div className="space-y-4">
              {/* Formato de Vale Térmico con Firmas */}
              <div className="bg-white text-slate-900 font-mono p-5 rounded-2xl shadow-xl max-w-md mx-auto border border-slate-300 text-xs">
                <div className="text-center border-b border-dashed border-slate-400 pb-3 mb-3">
                  <h3 className="font-black text-base tracking-wider">MR. BURGER - GOURMET</h3>
                  <p className="text-[10px] uppercase font-bold text-slate-600">CALI, COLOMBIA • COMPROBANTE DE CAJA</p>
                  <p className="font-bold text-xs mt-1 text-slate-800">
                    {selectedMov.tipo === 'SALIDA'
                      ? '*** CAJA - RETIRO DE EFECTIVO ***'
                      : '*** CAJA - DEPOSITO DE EFECTIVO ***'}
                  </p>
                </div>

                <div className="space-y-1 text-[11px] mb-3 border-b border-dashed border-slate-400 pb-3">
                  <div className="flex justify-between">
                    <span>FOLIO #:</span>
                    <strong className="font-bold">{selectedMov.id}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span>FECHA/HORA:</span>
                    <span>{new Date(selectedMov.creado_en).toLocaleString('es-CO')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>CATEGORIA:</span>
                    <span>{selectedMov.categoria}</span>
                  </div>
                  {selectedMov.concepto && (
                    <div className="flex justify-between">
                      <span>CONCEPTO:</span>
                      <strong className="font-bold">{selectedMov.concepto}</strong>
                    </div>
                  )}
                </div>

                <div className="mb-4 text-[11px]">
                  <span className="font-bold block mb-0.5">DETALLE / REFERENCIA:</span>
                  <p className="bg-slate-100 p-1.5 rounded text-slate-800">{selectedMov.descripcion}</p>
                </div>

                <div className="bg-slate-100 p-2 rounded text-center mb-6 border border-slate-300">
                  <span className="text-[10px] text-slate-600 block uppercase">IMPORTE NUMÉRICO:</span>
                  <div className="text-xl font-black text-slate-950 font-mono">
                    ${Number(selectedMov.valor).toLocaleString('es-CO')} COP
                  </div>
                </div>

                {/* 3 Espacios de Firmas Requeridos por el Cliente */}
                <div className="pt-2 border-t border-dashed border-slate-400 space-y-5 text-[10px] text-center font-bold">
                  <div>
                    <div className="w-3/4 mx-auto border-b border-slate-900 pb-1"></div>
                    <span className="block mt-1">ENTREGÓ (CAJERO)</span>
                  </div>
                  <div>
                    <div className="w-3/4 mx-auto border-b border-slate-900 pb-1"></div>
                    <span className="block mt-1">RECIBIÓ (BENEFICIARIO)</span>
                  </div>
                  <div>
                    <div className="w-3/4 mx-auto border-b border-slate-900 pb-1"></div>
                    <span className="block mt-1">AUTORIZÓ (ADMINISTRADOR)</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-center gap-3">
                <button
                  type="button"
                  onClick={() => setIsTirillaOpen(true)}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 cursor-pointer transition"
                >
                  <Printer className="w-4 h-4 text-amber-400" />
                  <span>Imprimir Vale Térmico (80mm)</span>
                </button>
                <button
                  type="button"
                  onClick={() => setVista('LISTA')}
                  className="px-5 py-2.5 rounded-xl text-xs font-bold bg-sky-600 hover:bg-sky-500 text-white cursor-pointer transition"
                >
                  Volver al Listado
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {selectedMov && (
        <TirillaModal
          isOpen={isTirillaOpen}
          onClose={() => setIsTirillaOpen(false)}
          tipo="VALE"
          datosVale={{
            restaurante: 'MR. BURGER',
            folio: selectedMov.id,
            fecha: new Date(selectedMov.creado_en).toLocaleString('es-CO'),
            tipo: selectedMov.tipo,
            categoria: selectedMov.categoria,
            concepto: selectedMov.concepto || 'GASTO OPERATIVO',
            descripcion: selectedMov.descripcion,
            valor: Number(selectedMov.valor),
            autorizado_por: 'Administrador'
          }}
        />
      )}
    </div>
  )
}
