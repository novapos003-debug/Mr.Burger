import React from 'react'
import type { CierreOut } from '../../types/caja'
import {
  Store,
  DollarSign,
  Lock,
  Unlock,
  Receipt,
  FileSpreadsheet,
  PlusCircle,
  RefreshCw,
  LogOut,
  Printer,
  Truck,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

interface Props {
  turno: CierreOut | null
  onAbrirTurnoClick: () => void
  onCerrarTurnoClick: () => void
  onMovimientosClick: () => void
  onValesClick: () => void
  onNuevoPedidoClick: () => void
  onCompraClick: () => void
  onConfigImpresoraClick: () => void
  onRefresh: () => void
  isRefreshing: boolean
  totalValesPendientes: number
}

export const CajaHeader: React.FC<Props> = ({
  turno,
  onAbrirTurnoClick,
  onCerrarTurnoClick,
  onMovimientosClick,
  onValesClick,
  onNuevoPedidoClick,
  onCompraClick,
  onConfigImpresoraClick,
  onRefresh,
  isRefreshing,
  totalValesPendientes,
}) => {
  const { logout, user } = useAuth()

  return (
    <header className="bg-slate-900 border-b border-slate-800 px-4 py-3 sticky top-0 z-30 shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Marca Mr. Burger POS & Estado del Turno */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/50 flex items-center justify-center text-emerald-400 shrink-0">
            <Store className="w-6 h-6" />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-black text-white tracking-wide uppercase">
                Mr. Burger <span className="text-emerald-400">POS CAJA</span>
              </h1>

              {/* Pill del Turno de Caja */}
              {turno ? (
                <div
                  className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-black tracking-wide bg-emerald-950 text-emerald-400 border border-emerald-500/50"
                  title={`Turno abierto desde ${new Date(turno.abierto_en).toLocaleTimeString()}`}
                >
                  <Unlock className="w-3 h-3 text-emerald-400" />
                  <span>TURNO #{turno.id} ACTIVO</span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-black tracking-wide bg-rose-950 text-rose-400 border border-rose-500/50">
                  <Lock className="w-3 h-3 text-rose-400" />
                  <span>CAJA CERRADA</span>
                </div>
              )}
            </div>

            <p className="text-[11px] text-slate-400 font-medium">
              Cajero: <strong className="text-slate-200">{user?.nombre || 'Caja'}</strong> • Terminal de Cobro, Mostrador y Arqueo
            </p>
          </div>
        </div>

        {/* Botones de Acción Operativa */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Botón Nuevo Pedido Mostrador / Domicilio / DiDi */}
          <button
            onClick={onNuevoPedidoClick}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-bold text-xs bg-amber-500 hover:bg-amber-400 active:scale-95 text-slate-950 shadow-md transition cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Nuevo Pedido</span>
          </button>

          {/* Vales / Pagarés */}
          <button
            onClick={onValesClick}
            className="relative flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-semibold text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 transition cursor-pointer"
            title="Ver pagarés y consumos pendientes por cobrar"
          >
            <Receipt className="w-4 h-4 text-purple-400" />
            <span>Vales</span>
            {totalValesPendientes > 0 && (
              <span className="w-5 h-5 rounded-full bg-purple-600 text-white font-black text-[10px] flex items-center justify-center">
                {totalValesPendientes}
              </span>
            )}
          </button>

          {/* Movimientos de Caja Menor (Gastos Operativos, Retiros y Depósitos) */}
          <button
            onClick={onMovimientosClick}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-black text-xs bg-rose-950/80 hover:bg-rose-900 border border-rose-700/80 text-rose-300 shadow-md transition cursor-pointer"
            title="Registrar gastos operativos (jabón Axion, esponjas, papel higiénico, insumos) o salidas de caja"
          >
            <FileSpreadsheet className="w-4 h-4 text-rose-400" />
            <span>💸 Gastos / Salidas</span>
          </button>

          {/* Ingresar la factura del pedido que llega del proveedor */}
          <button
            onClick={onCompraClick}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-bold text-xs bg-sky-950/80 hover:bg-sky-900 border border-sky-700/80 text-sky-300 shadow-md transition cursor-pointer"
            title="Ingresar la factura de un pedido de proveedor: sube las existencias de los insumos"
          >
            <Truck className="w-4 h-4 text-sky-400" />
            <span>Ingresar Factura</span>
          </button>

          {/* Botón Abrir / Cerrar Turno */}
          {turno ? (
            <button
              onClick={onCerrarTurnoClick}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-bold text-xs bg-rose-950/80 hover:bg-rose-900 border border-rose-700 text-rose-300 shadow-md transition cursor-pointer"
              title="Realizar arqueo a ciegas y cierre Z del turno"
            >
              <Lock className="w-4 h-4" />
              <span>Arqueo / Cierre Z</span>
            </button>
          ) : (
            <button
              onClick={onAbrirTurnoClick}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-bold text-xs bg-emerald-600 hover:bg-emerald-500 text-white shadow-md transition cursor-pointer"
              title="Abrir turno con base inicial de efectivo"
            >
              <DollarSign className="w-4 h-4" />
              <span>Abrir Turno</span>
            </button>
          )}

          {/* Configurar Impresora & Gaveta */}
          <button
            onClick={onConfigImpresoraClick}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-bold text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 shadow-md transition cursor-pointer"
            title="Configurar impresora térmica (58mm/80mm) y apertura de gaveta de dinero"
          >
            <Printer className="w-4 h-4 text-sky-400" />
            <span>Impresora</span>
          </button>

          {/* Refrescar */}
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white transition cursor-pointer disabled:opacity-50"
            title="Refrescar pedidos de caja"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
          </button>

          {/* Salir */}
          <button
            onClick={logout}
            className="p-2 rounded-xl bg-rose-950/40 hover:bg-rose-900/60 border border-rose-800/40 text-rose-400 hover:text-rose-300 transition cursor-pointer"
            title="Cerrar sesión"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  )
}
