import React, { useState } from 'react'
import {
  X,
  Printer,
  FileText,
  CheckCircle2,
  AlertCircle,
  Scissors
} from 'lucide-react'
import {
  imprimirHtmlTirilla,
  imprimirTirillaTermica,
  numeroALetras,
  getPrinterConfig,
  type DatosReciboVenta,
  type DatosValeRetiro,
  type DatosReporteZ
} from '../../utils/printer'

export type TipoTirilla = 'RECIBO' | 'VALE' | 'REPORTE_Z'

interface TirillaModalProps {
  isOpen: boolean
  onClose: () => void
  tipo: TipoTirilla
  datosRecibo?: DatosReciboVenta
  datosVale?: DatosValeRetiro
  datosReporteZ?: DatosReporteZ
}

export const TirillaModal: React.FC<TirillaModalProps> = ({
  isOpen,
  onClose,
  tipo,
  datosRecibo,
  datosVale,
  datosReporteZ
}) => {
  const [feedback, setFeedback] = useState<{ tipo: 'ok' | 'err'; msg: string } | null>(null)
  const [imprimiendoUsb, setImprimiendoUsb] = useState(false)

  if (!isOpen) return null

  // Generador de texto plano para ESC/POS
  const renderPlainText = (): string => {
    if (tipo === 'RECIBO' && datosRecibo) {
      let t = ''
      t += '         MR. BURGER RESTAURANTE         \n'
      t += '   SIMPLE POR FUERA. INTELIGENTE POR DENTRO   \n'
      t += '------------------------------------------\n'
      if (datosRecibo.leyenda_tributaria) {
        t += `  ${datosRecibo.leyenda_tributaria}\n`
      } else if (datosRecibo.iva_porcentaje > 0 && datosRecibo.iva_valor > 0) {
        t += `  Régimen Responsable de IVA (${datosRecibo.iva_porcentaje}%)\n`
      } else {
        t += '  Régimen No Responsable de IVA (Art. 512-13 E.T.)\n'
      }
      t += '       Documento de Control Interno       \n'
      t += `NIT: ${datosRecibo.nit} - ${datosRecibo.ciudad}\n`
      t += `Tel: ${datosRecibo.telefono}\n`
      t += `Dir: ${datosRecibo.direccion}\n`
      t += '------------------------------------------\n'
      t += `ORDEN: #${datosRecibo.consecutivo}    CANAL: ${datosRecibo.canal}\n`
      if (datosRecibo.mesa_numero) t += `MESA: ${datosRecibo.mesa_numero}\n`
      if (datosRecibo.cliente) t += `CLIENTE: ${datosRecibo.cliente}\n`
      if (datosRecibo.direccion_entrega) t += `ENTREGA: ${datosRecibo.direccion_entrega}\n`
      t += `FECHA: ${datosRecibo.fecha}\n`
      t += '==========================================\n'
      t += 'CANT DESCRIPCION               TOTAL\n'
      t += '------------------------------------------\n'
      datosRecibo.items.forEach((item) => {
        const lineaNombre = item.nombre.padEnd(26, ' ').slice(0, 26)
        const totalStr = `$${Number(item.total).toLocaleString('es-CO')}`.padStart(10, ' ')
        t += `${item.cantidad}x   ${lineaNombre}${totalStr}\n`
        if (item.variaciones && item.variaciones.length > 0) {
          t += `     > ${item.variaciones.join(', ')}\n`
        }
      })
      t += '==========================================\n'
      if (datosRecibo.iva_porcentaje > 0 && datosRecibo.iva_valor > 0) {
        t += `SUBTOTAL:                  $${Number(datosRecibo.subtotal).toLocaleString('es-CO')}\n`
        t += `IVA (${datosRecibo.iva_porcentaje}% INCLUIDO): $${Number(datosRecibo.iva_valor).toLocaleString('es-CO')}\n`
      } else {
        t += `SUBTOTAL:                  $${Number(datosRecibo.subtotal || datosRecibo.total).toLocaleString('es-CO')}\n`
        t += `IVA:                       Exento (0%)\n`
      }
      if (datosRecibo.recargo_empaque && Number(datosRecibo.recargo_empaque) > 0) {
        t += `EMPAQUE PARA LLEVAR:       +$${Number(datosRecibo.recargo_empaque).toLocaleString('es-CO')}\n`
      }
      t += `TOTAL A PAGAR:             $${Number(datosRecibo.total).toLocaleString('es-CO')}\n`
      t += '------------------------------------------\n'
      datosRecibo.pagos.forEach((p) => {
        t += `FORMA PAGO: ${p.metodo.padEnd(16, ' ')} $${Number(p.monto).toLocaleString('es-CO')}\n`
        if (p.recibido) t += `RECIBIDO:                  $${Number(p.recibido).toLocaleString('es-CO')}\n`
        if (p.cambio) t += `CAMBIO:                    $${Number(p.cambio).toLocaleString('es-CO')}\n`
      })
      t += '==========================================\n'
      t += '       GRACIAS POR SU PREFERENCIA        \n'
      t += '         mrburger.pos.local/cali          \n\n'
      return t
    }

    if (tipo === 'VALE' && datosVale) {
      let t = ''
      t += '              MR. BURGER                \n'
      t += `   COMPROBANTE DE ${datosVale.tipo === 'SALIDA' ? 'RETIRO' : 'INGRESO'} DE CAJA   \n`
      t += `FOLIO: #${datosVale.folio}    FECHA: ${datosVale.fecha}\n`
      t += '------------------------------------------\n'
      t += `CATEGORIA: ${datosVale.categoria}\n`
      t += `CONCEPTO:  ${datosVale.concepto}\n`
      t += `VALOR:     $${Number(datosVale.valor).toLocaleString('es-CO')} COP\n`
      t += `SON: ${numeroALetras(datosVale.valor)}\n`
      t += `MOTIVO:    ${datosVale.descripcion}\n`
      t += '------------------------------------------\n\n\n'
      t += ' ___________    ___________    ___________\n'
      t += '   ENTREGO        RECIBIO        AUTORIZO \n\n'
      return t
    }

    if (tipo === 'REPORTE_Z' && datosReporteZ) {
      let t = ''
      t += '              MR. BURGER                \n'
      t += '        REPORTE Z - CIERRE DE TURNO       \n'
      t += `TURNO: #${datosReporteZ.turno_id}   CAJERO: ${datosReporteZ.cajero}\n`
      t += `APERTURA: ${datosReporteZ.fecha_apertura}\n`
      t += `CIERRE:   ${datosReporteZ.fecha_cierre}\n`
      t += '==========================================\n'
      t += `BASE INICIAL:              $${Number(datosReporteZ.monto_inicial).toLocaleString('es-CO')}\n`
      t += `TOTAL VENTAS:              $${Number(datosReporteZ.total_ventas).toLocaleString('es-CO')}\n`
      t += `  - Comida:                $${Number(datosReporteZ.total_venta_comida).toLocaleString('es-CO')}\n`
      t += `  - Bebidas:               $${Number(datosReporteZ.total_venta_bebida).toLocaleString('es-CO')}\n`
      t += '------------------------------------------\n'
      t += 'DESGLOSE FORMAS DE PAGO:\n'
      t += `  - Efectivo:              $${Number(datosReporteZ.total_efectivo).toLocaleString('es-CO')}\n`
      t += `  - Tarjeta Datáfono:      $${Number(datosReporteZ.total_tarjeta).toLocaleString('es-CO')}\n`
      t += `  - Transferencia:         $${Number(datosReporteZ.total_transferencia).toLocaleString('es-CO')}\n`
      t += `  - DiDi Tarjeta (Virtual):$${Number(datosReporteZ.total_didi_tarjeta).toLocaleString('es-CO')}\n`
      t += `  - DiDi Efectivo:         $${Number(datosReporteZ.total_didi_efectivo).toLocaleString('es-CO')}\n`
      t += `  - Vales (Por Cobrar):    $${Number(datosReporteZ.total_vale).toLocaleString('es-CO')}\n`
      t += '------------------------------------------\n'
      t += `SALIDAS CAJA MENOR:       -$${Number(datosReporteZ.total_salidas_caja).toLocaleString('es-CO')}\n`
      t += `ENTRADAS CAJA MENOR:      +$${Number(datosReporteZ.total_entradas_caja).toLocaleString('es-CO')}\n`
      t += `DEVOLUCIONES:             -$${Number(datosReporteZ.total_devoluciones).toLocaleString('es-CO')}\n`
      t += '==========================================\n'
      t += `EFECTIVO ESPERADO CAJON:   $${Number(datosReporteZ.efectivo_esperado).toLocaleString('es-CO')}\n`
      if (datosReporteZ.efectivo_declarado !== undefined) {
        t += `EFECTIVO DECLARADO (ARQUEO):$${Number(datosReporteZ.efectivo_declarado).toLocaleString('es-CO')}\n`
        const dif = datosReporteZ.diferencia ?? (datosReporteZ.efectivo_declarado - datosReporteZ.efectivo_esperado)
        t += `DIFERENCIA (FALT/SOBR):    $${Number(dif).toLocaleString('es-CO')}\n`
      }
      t += '------------------------------------------\n'
      t += `PREPARADOS: Reusados: ${datosReporteZ.preparados_reutilizados} | Descartados: ${datosReporteZ.preparados_descartados}\n`
      t += '==========================================\n'
      t += '         FOTOGRAMA INMUTABLE POSTGRES     \n\n'
      return t
    }

    return ''
  }

  // Generador de HTML para vista previa e impresión de navegador
  const renderHtmlPreview = () => {
    if (tipo === 'RECIBO' && datosRecibo) {
      return (
        <div className="text-left font-mono text-[11px] leading-tight space-y-2 select-text">
          <div className="text-center pb-2 border-b border-dashed border-slate-700">
            <h2 className="text-sm font-black tracking-wider text-slate-900">MR. BURGER</h2>
            <p className="text-[10px] text-slate-600 font-sans italic">{datosRecibo.lema}</p>
            <div className="my-1 py-0.5 px-2 bg-slate-100 rounded border border-slate-200 inline-block">
              {datosRecibo.iva_porcentaje > 0 && datosRecibo.iva_valor > 0 ? (
                <>
                  <p className="text-[9px] font-bold text-slate-800 uppercase tracking-tight">Régimen Responsable de IVA</p>
                  <p className="text-[8px] text-slate-500">Tarifa IVA {datosRecibo.iva_porcentaje}% Incluido</p>
                </>
              ) : (
                <>
                  <p className="text-[9px] font-bold text-slate-800 uppercase tracking-tight">Régimen No Responsable de IVA</p>
                  <p className="text-[8px] text-slate-500">Documento de Control Interno (Art. 512-13 E.T. - Tarifa 0%)</p>
                </>
              )}
            </div>
            <p className="text-[10px] text-slate-600">NIT: {datosRecibo.nit} • Cali, Valle</p>
            <p className="text-[10px] text-slate-600">Tel: {datosRecibo.telefono} • Dir: {datosRecibo.direccion}</p>
          </div>

          <div className="text-[10px] text-slate-700 space-y-0.5 pt-1">
            <div className="flex justify-between font-bold">
              <span>ORDEN #{datosRecibo.consecutivo}</span>
              <span className="uppercase">{datosRecibo.canal} {datosRecibo.mesa_numero ? `• MESA ${datosRecibo.mesa_numero}` : ''}</span>
            </div>
            {datosRecibo.cliente && <div>Cliente: {datosRecibo.cliente}</div>}
            {datosRecibo.direccion_entrega && <div>Entrega: {datosRecibo.direccion_entrega}</div>}
            <div>Fecha: {datosRecibo.fecha}</div>
          </div>

          <div className="border-t-2 border-b-2 border-slate-800 py-1 my-2">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="border-b border-dashed border-slate-400 font-bold">
                  <th className="text-left pb-1">CANT</th>
                  <th className="text-left pb-1">DESCRIPCION</th>
                  <th className="text-right pb-1">TOTAL</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dashed divide-slate-300">
                {datosRecibo.items.map((item, idx) => (
                  <tr key={idx}>
                    <td className="align-top font-bold py-1 w-8">{item.cantidad}x</td>
                    <td className="py-1">
                      <div className="font-bold text-slate-900">{item.nombre}</div>
                      {item.variaciones && item.variaciones.length > 0 && (
                        <div className="text-[9px] text-slate-500 italic">
                          {item.variaciones.join(', ')}
                        </div>
                      )}
                    </td>
                    <td className="text-right align-top py-1 font-bold">
                      ${Number(item.total).toLocaleString('es-CO')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="space-y-1 text-[11px] pt-1 border-b border-dashed border-slate-700 pb-2">
            {datosRecibo.iva_porcentaje > 0 && datosRecibo.iva_valor > 0 ? (
              <>
                <div className="flex justify-between">
                  <span className="text-slate-600">Subtotal:</span>
                  <span>${Number(datosRecibo.subtotal).toLocaleString('es-CO')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">IVA ({datosRecibo.iva_porcentaje}% Incluido):</span>
                  <span>${Number(datosRecibo.iva_valor).toLocaleString('es-CO')}</span>
                </div>
              </>
            ) : (
              <>
                <div className="flex justify-between text-slate-600">
                  <span>Subtotal:</span>
                  <span>${Number(datosRecibo.subtotal || datosRecibo.total).toLocaleString('es-CO')}</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>IVA:</span>
                  <span className="font-semibold text-slate-700">Exento (0%)</span>
                </div>
              </>
            )}
            {datosRecibo.recargo_empaque && Number(datosRecibo.recargo_empaque) > 0 && (
              <div className="flex justify-between font-bold text-orange-600">
                <span>Empaque Para Llevar:</span>
                <span>+${Number(datosRecibo.recargo_empaque).toLocaleString('es-CO')}</span>
              </div>
            )}
            <div className="flex justify-between font-black text-sm text-slate-950 pt-1 border-t border-slate-800">
              <span>TOTAL A PAGAR:</span>
              <span>${Number(datosRecibo.total).toLocaleString('es-CO')}</span>
            </div>
          </div>

          <div className="text-[10px] space-y-0.5 pt-1">
            {datosRecibo.pagos.map((p, idx) => (
              <div key={idx} className="space-y-0.5">
                <div className="flex justify-between font-bold">
                  <span>PAGO: {p.metodo}</span>
                  <span>${Number(p.monto).toLocaleString('es-CO')}</span>
                </div>
                {p.recibido && (
                  <div className="flex justify-between text-slate-600">
                    <span>Efectivo Recibido:</span>
                    <span>${Number(p.recibido).toLocaleString('es-CO')}</span>
                  </div>
                )}
                {p.cambio && (
                  <div className="flex justify-between font-bold text-slate-900">
                    <span>Cambio Devuelto:</span>
                    <span>${Number(p.cambio).toLocaleString('es-CO')}</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="text-center pt-4 text-[10px] text-slate-600 space-y-0.5">
            <p className="font-bold">¡GRACIAS POR SU VISITA!</p>
            <p className="text-[9px]">Mr. Burger • Cali, Valle del Cauca</p>
          </div>
        </div>
      )
    }

    if (tipo === 'VALE' && datosVale) {
      return (
        <div className="text-left font-mono text-[11px] leading-tight space-y-3 select-text">
          <div className="text-center pb-2 border-b border-dashed border-slate-700">
            <h2 className="text-sm font-black text-slate-900">MR. BURGER</h2>
            <p className="text-xs font-bold uppercase text-slate-800">
              {datosVale.tipo === 'SALIDA' ? 'COMPROBANTE DE RETIRO (EGRESO)' : 'COMPROBANTE DE INGRESO'}
            </p>
            <p className="text-[10px] text-slate-600">Caja Menor • Control Operativo</p>
          </div>

          <div className="text-[11px] space-y-1">
            <div className="flex justify-between">
              <span className="font-bold">FOLIO: #{datosVale.folio}</span>
              <span>{datosVale.fecha}</span>
            </div>
            <div><span className="font-semibold text-slate-600">CATEGORÍA:</span> {datosVale.categoria}</div>
            <div><span className="font-semibold text-slate-600">CONCEPTO:</span> <strong className="text-slate-900">{datosVale.concepto}</strong></div>
            <div className="text-xs font-black text-slate-950 p-2 bg-slate-100 rounded border border-slate-300 flex justify-between">
              <span>VALOR:</span>
              <span>${Number(datosVale.valor).toLocaleString('es-CO')} COP</span>
            </div>
            <div className="text-[10px] text-slate-700">
              <span className="font-semibold">SON: </span>
              {numeroALetras(datosVale.valor)}
            </div>
            <div className="text-[10px] text-slate-700 pt-1 border-t border-dashed border-slate-300">
              <span className="font-semibold">DETALLE: </span>
              {datosVale.descripcion}
            </div>
          </div>

          {/* Tres firmas obligatorias */}
          <div className="pt-6 grid grid-cols-3 gap-2 text-center text-[9px] border-t border-slate-400">
            <div className="border-t border-slate-800 pt-1 font-bold">
              ENTREGÓ
            </div>
            <div className="border-t border-slate-800 pt-1 font-bold">
              RECIBIÓ
            </div>
            <div className="border-t border-slate-800 pt-1 font-bold">
              AUTORIZÓ
            </div>
          </div>
        </div>
      )
    }

    if (tipo === 'REPORTE_Z' && datosReporteZ) {
      return (
        <div className="text-left font-mono text-[11px] leading-tight space-y-2 select-text">
          <div className="text-center pb-2 border-b border-dashed border-slate-700">
            <h2 className="text-sm font-black text-slate-900">MR. BURGER</h2>
            <p className="text-xs font-bold text-slate-800">REPORTE Z • CIERRE DE TURNO</p>
            <p className="text-[10px] text-slate-600">TURNO #{datosReporteZ.turno_id} • CAJERO: {datosReporteZ.cajero}</p>
          </div>

          <div className="text-[10px] text-slate-600 space-y-0.5">
            <div>Apertura: {datosReporteZ.fecha_apertura}</div>
            <div>Cierre: {datosReporteZ.fecha_cierre}</div>
          </div>

          <div className="border-t border-b border-slate-800 py-1 space-y-1 text-[11px]">
            <div className="flex justify-between">
              <span>Base Inicial:</span>
              <span className="font-bold">${Number(datosReporteZ.monto_inicial).toLocaleString('es-CO')}</span>
            </div>
            <div className="flex justify-between font-black text-slate-900 pt-0.5 border-t border-dashed border-slate-400">
              <span>TOTAL VENTAS:</span>
              <span>${Number(datosReporteZ.total_ventas).toLocaleString('es-CO')}</span>
            </div>
            <div className="flex justify-between text-[10px] text-slate-600 pl-2">
              <span>• Venta Comidas:</span>
              <span>${Number(datosReporteZ.total_venta_comida).toLocaleString('es-CO')}</span>
            </div>
            <div className="flex justify-between text-[10px] text-slate-600 pl-2">
              <span>• Venta Bebidas:</span>
              <span>${Number(datosReporteZ.total_venta_bebida).toLocaleString('es-CO')}</span>
            </div>
          </div>

          <div className="space-y-1 text-[10px] py-1 border-b border-slate-800">
            <p className="font-bold text-slate-900 uppercase">Formas de Pago:</p>
            <div className="flex justify-between pl-2">
              <span>Efectivo:</span>
              <span className="font-bold">${Number(datosReporteZ.total_efectivo).toLocaleString('es-CO')}</span>
            </div>
            <div className="flex justify-between pl-2">
              <span>Tarjeta Datáfono:</span>
              <span>${Number(datosReporteZ.total_tarjeta).toLocaleString('es-CO')}</span>
            </div>
            <div className="flex justify-between pl-2">
              <span>Transferencia:</span>
              <span>${Number(datosReporteZ.total_transferencia).toLocaleString('es-CO')}</span>
            </div>
            <div className="flex justify-between pl-2">
              <span>DiDi Tarjeta (Por Cobrar):</span>
              <span>${Number(datosReporteZ.total_didi_tarjeta).toLocaleString('es-CO')}</span>
            </div>
            <div className="flex justify-between pl-2">
              <span>DiDi Efectivo (Repartidor):</span>
              <span>${Number(datosReporteZ.total_didi_efectivo).toLocaleString('es-CO')}</span>
            </div>
            <div className="flex justify-between pl-2">
              <span>Vales Pendientes:</span>
              <span>${Number(datosReporteZ.total_vale).toLocaleString('es-CO')}</span>
            </div>
          </div>

          <div className="space-y-1 text-[10px] py-1 border-b border-slate-800">
            <div className="flex justify-between text-red-700">
              <span>(-) Salidas Caja Menor:</span>
              <span className="font-bold">-${Number(datosReporteZ.total_salidas_caja).toLocaleString('es-CO')}</span>
            </div>
            <div className="flex justify-between text-emerald-700">
              <span>(+) Entradas Caja Menor:</span>
              <span>+${Number(datosReporteZ.total_entradas_caja).toLocaleString('es-CO')}</span>
            </div>
            {datosReporteZ.total_devoluciones > 0 && (
              <div className="flex justify-between text-red-700">
                <span>(-) Devoluciones en Caja:</span>
                <span>-${Number(datosReporteZ.total_devoluciones).toLocaleString('es-CO')}</span>
              </div>
            )}
          </div>

          <div className="p-2 bg-slate-100 rounded border border-slate-300 space-y-1 text-[11px]">
            <div className="flex justify-between font-black text-slate-900">
              <span>EFECTIVO ESPERADO:</span>
              <span>${Number(datosReporteZ.efectivo_esperado).toLocaleString('es-CO')}</span>
            </div>
            {datosReporteZ.efectivo_declarado !== undefined && (
              <>
                <div className="flex justify-between text-[10px] text-slate-700">
                  <span>Efectivo Declarado:</span>
                  <span>${Number(datosReporteZ.efectivo_declarado).toLocaleString('es-CO')}</span>
                </div>
                {(() => {
                  const dif = datosReporteZ.diferencia ?? (datosReporteZ.efectivo_declarado - datosReporteZ.efectivo_esperado)
                  return (
                    <div className={`flex justify-between font-bold text-xs ${dif < 0 ? 'text-red-600' : dif > 0 ? 'text-emerald-600' : 'text-slate-800'}`}>
                      <span>{dif < 0 ? 'FALTANTE EN CAJA:' : dif > 0 ? 'SOBRANTE EN CAJA:' : 'CUADRE EXACTO:'}</span>
                      <span>${Number(dif).toLocaleString('es-CO')}</span>
                    </div>
                  )
                })()}
              </>
            )}
          </div>

          <div className="text-[9px] text-slate-500 pt-1">
            Preparados Reutilizados: {datosReporteZ.preparados_reutilizados} • Descartados: {datosReporteZ.preparados_descartados}
          </div>
        </div>
      )
    }

    return null
  }

  const handlePrintWebUsb = async () => {
    setImprimiendoUsb(true)
    setFeedback(null)
    try {
      const res = await imprimirTirillaTermica(renderPlainText())
      if (res.success) {
        setFeedback({ tipo: 'ok', msg: res.message })
      } else {
        setFeedback({ tipo: 'err', msg: res.message })
      }
    } catch (err: any) {
      setFeedback({ tipo: 'err', msg: err.message || 'Error al conectar con la impresora USB' })
    } finally {
      setImprimiendoUsb(false)
    }
  }

  const handlePrintBrowser = () => {
    const plain = renderPlainText()
    const htmlLines = plain.replace(/\n/g, '<br/>')
    imprimirHtmlTirilla(`<div>${htmlLines}</div>`)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl flex flex-col max-h-[92vh]">
        {/* Header Modal */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-950">
          <div className="flex items-center gap-2 text-slate-100 font-bold text-sm">
            <Printer className="w-4 h-4 text-orange-400" />
            <span>
              {tipo === 'RECIBO' && `Tirilla Térmica ${getPrinterConfig().tamanoPapel} • Recibo de Venta`}
              {tipo === 'VALE' && `Tirilla Térmica ${getPrinterConfig().tamanoPapel} • Vale de Caja Menor`}
              {tipo === 'REPORTE_Z' && `Tirilla Térmica ${getPrinterConfig().tamanoPapel} • Reporte Z Cierre`}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Feedback visual */}
        {feedback && (
          <div
            className={`p-3 text-xs flex items-center gap-2 ${
              feedback.tipo === 'ok'
                ? 'bg-emerald-950/80 border-b border-emerald-800 text-emerald-200'
                : 'bg-amber-950/80 border-b border-amber-800 text-amber-200'
            }`}
          >
            {feedback.tipo === 'ok' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
            )}
            <span>{feedback.msg}</span>
          </div>
        )}

        {/* Simulación Realista de Papel Térmico 80mm */}
        <div className="flex-1 overflow-y-auto p-4 bg-slate-950 flex justify-center">
          <div className="w-[300px] bg-[#fffbf0] text-slate-900 shadow-2xl rounded-sm p-4 relative border-t-4 border-slate-400">
            {/* Corte dentado superior */}
            <div className="absolute top-0 left-0 right-0 h-1 flex justify-between overflow-hidden opacity-30">
              {Array.from({ length: 30 }).map((_, i) => (
                <span key={i} className="text-[6px] -mt-1 font-mono">▲</span>
              ))}
            </div>

            {/* Contenido de la tirilla */}
            {renderHtmlPreview()}

            {/* Corte dentado inferior */}
            <div className="mt-6 pt-2 border-t border-dashed border-slate-400 flex items-center justify-between text-[8px] text-slate-500">
              <span className="flex items-center gap-1">
                <Scissors className="w-3 h-3" /> Corte automático 80mm
              </span>
              <span>Mr. Burger POS</span>
            </div>
          </div>
        </div>

        {/* Botones de acción de impresión */}
        <div className="p-4 border-t border-slate-800 bg-slate-950 flex flex-col sm:flex-row items-center gap-2">
          <button
            onClick={handlePrintWebUsb}
            disabled={imprimiendoUsb}
            className="w-full sm:flex-1 py-2.5 px-3 rounded-xl bg-orange-600 hover:bg-orange-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-orange-950/50 transition cursor-pointer disabled:opacity-50"
          >
            <Printer className="w-4 h-4" />
            <span>Imprimir tirilla</span>
          </button>

          <button
            onClick={handlePrintBrowser}
            className="w-full sm:flex-1 py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs flex items-center justify-center gap-2 border border-slate-700 transition cursor-pointer"
          >
            <FileText className="w-4 h-4" />
            <span>Imprimir / PDF</span>
          </button>

          <button
            onClick={onClose}
            className="w-full sm:w-auto py-2.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white font-semibold text-xs border border-slate-800 transition cursor-pointer"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}
