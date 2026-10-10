import React, { useEffect, useState } from 'react'
import { AlertCircle, CheckCircle2, Loader2, Plus, Trash2, Truck, X } from 'lucide-react'
import { crearCompraCaja, getComprasRecientesCaja, getInsumosCaja } from '../../api/caja'
import type { InsumoCaja } from '../../api/caja'
import type { CompraOut } from '../../types/admin'

interface Props {
  isOpen: boolean
  onClose: () => void
}

interface Linea {
  ingrediente_id: number | ''
  cantidad: string
  costo_unitario: string
}

const IVA_TASA = 19
const lineaVacia = (): Linea => ({ ingrediente_id: '', cantidad: '', costo_unitario: '' })
const pesos = (n: number) => `$${n.toLocaleString('es-CO', { maximumFractionDigits: 2 })}`

/** Ingreso de la factura de un pedido que llega del proveedor. Sube las existencias de cada
 *  insumo y deja el movimiento en el kardex. Lo usan el cajero y el administrador. */
export const RegistrarCompraModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const [insumos, setInsumos] = useState<InsumoCaja[]>([])
  const [recientes, setRecientes] = useState<CompraOut[]>([])
  const [cargando, setCargando] = useState(false)
  const [proveedor, setProveedor] = useState('')
  const [factura, setFactura] = useState('')
  const [aplicaIva, setAplicaIva] = useState(false)
  const [lineas, setLineas] = useState<Linea[]>([lineaVacia()])
  const [guardando, setGuardando] = useState(false)
  const [aviso, setAviso] = useState<{ tipo: 'ok' | 'err'; msg: string } | null>(null)

  useEffect(() => {
    if (!isOpen) return
    setAviso(null)
    setProveedor('')
    setFactura('')
    setAplicaIva(false)
    setLineas([lineaVacia()])
    setCargando(true)
    Promise.all([getInsumosCaja(), getComprasRecientesCaja().catch(() => [])])
      .then(([ins, compras]) => {
        setInsumos(ins)
        setRecientes(compras)
      })
      .catch(() => setAviso({ tipo: 'err', msg: 'No se pudo cargar la lista de insumos. Revisa la conexión.' }))
      .finally(() => setCargando(false))
  }, [isOpen])

  if (!isOpen) return null

  const cambiar = (idx: number, campo: keyof Linea, valor: string) => {
    setLineas((prev) =>
      prev.map((l, i) =>
        i === idx ? { ...l, [campo]: campo === 'ingrediente_id' ? (valor ? Number(valor) : '') : valor } : l
      )
    )
  }

  const unidadDe = (id: number | '') => insumos.find((i) => i.id === id)?.unidad_base?.toLowerCase() || ''
  const subtotal = lineas.reduce((acc, l) => acc + (Number(l.cantidad) || 0) * (Number(l.costo_unitario) || 0), 0)
  const iva = aplicaIva ? (subtotal * IVA_TASA) / 100 : 0
  const total = subtotal + iva

  const guardar = async (e: React.FormEvent) => {
    e.preventDefault()
    setAviso(null)

    const validas = lineas.filter((l) => l.ingrediente_id !== '' || l.cantidad || l.costo_unitario)
    if (validas.length === 0) {
      setAviso({ tipo: 'err', msg: 'Agrega al menos un insumo de la factura.' })
      return
    }
    for (const l of validas) {
      if (l.ingrediente_id === '') {
        setAviso({ tipo: 'err', msg: 'Hay una línea sin insumo seleccionado.' })
        return
      }
      if (!(Number(l.cantidad) > 0)) {
        setAviso({ tipo: 'err', msg: 'Cada insumo necesita una cantidad mayor a 0.' })
        return
      }
      if (l.costo_unitario !== '' && Number(l.costo_unitario) < 0) {
        setAviso({ tipo: 'err', msg: 'El costo no puede ser negativo.' })
        return
      }
    }
    const repetidos = new Set<number>()
    for (const l of validas) {
      if (repetidos.has(l.ingrediente_id as number)) {
        setAviso({ tipo: 'err', msg: 'Un insumo está dos veces. Déjalo en una sola línea con la cantidad total.' })
        return
      }
      repetidos.add(l.ingrediente_id as number)
    }

    const descripcion = [
      `Proveedor: ${proveedor.trim()}`,
      factura.trim() ? `#Factura: ${factura.trim()}` : '',
      aplicaIva
        ? `Subtotal: ${pesos(subtotal)} | IVA (${IVA_TASA}%): ${pesos(iva)} | Total a Pagar: ${pesos(total)}`
        : `Total a Pagar: ${pesos(subtotal)}`,
    ]
      .filter(Boolean)
      .join('. ')
      .slice(0, 500)

    setGuardando(true)
    try {
      await crearCompraCaja({
        descripcion,
        detalles: validas.map((l) => ({
          ingrediente_id: l.ingrediente_id as number,
          cantidad: Number(l.cantidad),
          costo_unitario: Number(l.costo_unitario) || 0,
        })),
      })
      setAviso({ tipo: 'ok', msg: 'Factura ingresada. Las existencias ya subieron.' })
      setTimeout(onClose, 1500)
    } catch (err: any) {
      const detalle = err.response?.data?.detail
      setAviso({
        tipo: 'err',
        msg: typeof detalle === 'string' ? detalle : 'No se pudo ingresar la factura. Revisa los datos e intenta de nuevo.',
      })
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-3 sm:p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        <div className="p-4 border-b border-slate-800 bg-sky-950/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500/20 border border-sky-500/40 flex items-center justify-center text-sky-400">
              <Truck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-black text-white text-base sm:text-lg tracking-wide">Ingresar Factura de Proveedor</h2>
              <p className="text-xs text-sky-300/80">El pedido que llega: sube las existencias de cada insumo</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={guardar} className="p-4 sm:p-6 space-y-4 overflow-y-auto text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-bold mb-1">Proveedor:</label>
              <input
                type="text"
                required
                maxLength={120}
                value={proveedor}
                onChange={(e) => setProveedor(e.target.value)}
                placeholder="Ej. Panadería Central"
                className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-sky-500"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-bold mb-1"># Factura o remisión (opcional):</label>
              <input
                type="text"
                maxLength={60}
                value={factura}
                onChange={(e) => setFactura(e.target.value)}
                placeholder="Ej. 4092"
                className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-sky-500"
              />
            </div>
          </div>

          {cargando ? (
            <div className="flex items-center justify-center py-8 text-slate-400 gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-sky-400" />
              <span>Cargando insumos...</span>
            </div>
          ) : (
            <div className="border-t border-slate-800 pt-3 space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-bold text-slate-300">Lo que llegó:</span>
                <button
                  type="button"
                  onClick={() => setLineas((prev) => [...prev, lineaVacia()])}
                  className="flex items-center gap-1 text-sky-400 hover:text-sky-300 font-bold cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Agregar insumo</span>
                </button>
              </div>

              {lineas.map((linea, idx) => (
                <div key={idx} className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 grid grid-cols-12 gap-2 items-end">
                  <div className="col-span-12 sm:col-span-5">
                    <label className="block text-[10px] text-slate-500 mb-0.5">Insumo</label>
                    <select
                      value={linea.ingrediente_id}
                      onChange={(e) => cambiar(idx, 'ingrediente_id', e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-100 text-xs"
                    >
                      <option value="">Selecciona...</option>
                      {insumos.map((ing) => (
                        <option key={ing.id} value={ing.id}>
                          {ing.nombre} ({ing.unidad_base.toLowerCase()})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="col-span-5 sm:col-span-3">
                    <label className="block text-[10px] text-slate-500 mb-0.5">
                      Cantidad{unidadDe(linea.ingrediente_id) ? ` (${unidadDe(linea.ingrediente_id)})` : ''}
                    </label>
                    <input
                      type="number"
                      min="0"
                      step="any"
                      inputMode="decimal"
                      value={linea.cantidad}
                      onChange={(e) => cambiar(idx, 'cantidad', e.target.value)}
                      placeholder="0"
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-white font-mono text-xs text-center"
                    />
                  </div>
                  <div className="col-span-5 sm:col-span-3">
                    <label className="block text-[10px] text-slate-500 mb-0.5">
                      Costo por {unidadDe(linea.ingrediente_id) || 'unidad'}
                    </label>
                    <input
                      type="number"
                      min="0"
                      step="any"
                      inputMode="decimal"
                      value={linea.costo_unitario}
                      onChange={(e) => cambiar(idx, 'costo_unitario', e.target.value)}
                      placeholder="0"
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-emerald-400 font-mono text-xs text-right"
                    />
                  </div>
                  <div className="col-span-2 sm:col-span-1 flex justify-center pb-1.5">
                    {lineas.length > 1 && (
                      <button
                        type="button"
                        onClick={() => setLineas((prev) => prev.filter((_, i) => i !== idx))}
                        className="text-red-400 hover:text-red-300 cursor-pointer"
                        title="Quitar esta línea"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}

              <p className="text-[11px] text-slate-500">
                La cantidad va en la unidad del insumo (gramos, mililitros o unidades) y el costo es el de UNA de esas
                unidades. Ejemplo: 5 kilos de papa a $30.000 son 5000 gramos a $6 cada gramo. Si no sabes el costo,
                déjalo en 0 y no se cambia.
              </p>
            </div>
          )}

          <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
            <label className="flex items-center gap-2 cursor-pointer text-slate-200 font-bold select-none">
              <input
                type="checkbox"
                checked={aplicaIva}
                onChange={(e) => setAplicaIva(e.target.checked)}
                className="w-4 h-4 rounded cursor-pointer"
              />
              <span>La factura cobra IVA ({IVA_TASA}%) aparte</span>
            </label>
            {aplicaIva && (
              <div className="flex justify-between text-slate-400">
                <span>Subtotal + IVA:</span>
                <span className="font-mono">
                  {pesos(subtotal)} + {pesos(iva)}
                </span>
              </div>
            )}
            <div className="flex justify-between items-center font-bold pt-2 border-t border-slate-800">
              <span className="text-white uppercase tracking-wide">Total de la factura:</span>
              <span className="text-emerald-400 font-mono text-base font-black">{pesos(total)}</span>
            </div>
            <p className="text-[11px] text-slate-500">
              Esto NO saca plata de la caja. Si la factura se paga con efectivo del cajón, regístralo también en
              "Gastos / Salidas".
            </p>
          </div>

          {aviso && (
            <div
              className={`p-3 rounded-xl flex items-center gap-2 font-bold ${
                aviso.tipo === 'ok'
                  ? 'bg-emerald-950/60 border border-emerald-700 text-emerald-300'
                  : 'bg-rose-950/60 border border-rose-700 text-rose-300'
              }`}
            >
              {aviso.tipo === 'ok' ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
              <span>{aviso.msg}</span>
            </div>
          )}

          {recientes.length > 0 && (
            <div className="border-t border-slate-800 pt-3">
              <p className="font-bold text-slate-400 mb-1.5">Últimas facturas ingresadas (para no repetir):</p>
              <ul className="space-y-1">
                {recientes.map((c) => (
                  <li key={c.id} className="flex justify-between gap-3 text-[11px] text-slate-400">
                    <span className="truncate">
                      {new Date(c.creado_en).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })} ·{' '}
                      {c.usuario_nombre || '—'} · {(c.descripcion || '').split('. ').slice(0, 2).join(' · ')}
                    </span>
                    <span className="font-mono text-slate-300 shrink-0">{pesos(Number(c.costo_total) || 0)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl font-bold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition cursor-pointer"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={guardando || cargando}
              className="px-5 py-2.5 rounded-xl font-black text-white bg-sky-600 hover:bg-sky-500 active:scale-95 shadow-lg transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              {guardando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Truck className="w-4 h-4" />}
              <span>Ingresar factura</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
