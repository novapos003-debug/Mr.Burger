// Utilidad de Impresión Térmica 80mm ESC/POS y WebUSB para Mr. Burger
// Soporta:
// 1. Impresión directa por WebUSB (ESC/POS binario) en Windows y Android sin drivers
// 2. Impresión por diálogo del navegador (HTML optimizado para papel continuo de 80mm)

export interface ItemRecibo {
  cantidad: number
  nombre: string
  precio_unitario: number
  total: number
  variaciones?: string[]
}

export interface DatosReciboVenta {
  restaurante: string
  lema: string
  nit: string
  ciudad: string
  telefono: string
  direccion: string
  leyenda_tributaria?: string
  consecutivo: number
  fecha: string
  canal: string
  mesa_numero?: number | null
  cliente?: string | null
  direccion_entrega?: string | null
  items: ItemRecibo[]
  subtotal: number
  iva_porcentaje: number
  iva_valor: number
  total: number
  pagos: Array<{
    metodo: string
    monto: number
    recibido?: number
    cambio?: number
    referencia?: string
  }>
  cajero?: string
}

export interface DatosValeRetiro {
  restaurante: string
  folio: number
  fecha: string
  tipo: 'SALIDA' | 'ENTRADA'
  categoria: string
  concepto: string
  descripcion: string
  valor: number
  valor_letras?: string
  autorizado_por: string
}

export interface DatosReporteZ {
  restaurante: string
  turno_id: number
  fecha_apertura: string
  fecha_cierre: string
  cajero: string
  monto_inicial: number
  total_ventas: number
  total_venta_comida: number
  total_venta_bebida: number
  total_efectivo: number
  total_tarjeta: number
  total_transferencia: number
  total_didi_tarjeta: number
  total_didi_efectivo: number
  total_vale: number
  total_salidas_caja: number
  total_entradas_caja: number
  total_devoluciones: number
  efectivo_esperado: number
  efectivo_declarado?: number
  diferencia?: number
  preparados_reutilizados: number
  preparados_descartados: number
  notas?: string
}

// Convertir números a palabras en español para comprobantes contables
export function numeroALetras(num: number): string {
  const unidades = ['', 'UN', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE']
  const decenas = ['', 'DIEZ', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA']
  const especiales: Record<number, string> = {
    11: 'ONCE', 12: 'DOCE', 13: 'TRECE', 14: 'CATORCE', 15: 'QUINCE',
    16: 'DIECISEIS', 17: 'DIECISIETE', 18: 'DIECIOCHO', 19: 'DIECINUEVE',
    21: 'VEINTIUN', 22: 'VEINTIDOS', 23: 'VEINTITRES', 24: 'VEINTICUATRO',
    25: 'VEINTICINCO', 26: 'VEINTISEIS', 27: 'VEINTISIETE', 28: 'VEINTIOCHO', 29: 'VEINTINUEVE'
  }

  if (num === 0) return 'CERO PESOS M/CTE'
  const entero = Math.floor(Math.abs(num))

  const seccion = (n: number): string => {
    let out = ''
    const c = Math.floor(n / 100)
    const d = Math.floor((n % 100) / 10)
    const u = n % 10
    const resto = n % 100

    if (c > 0) {
      if (c === 1 && resto === 0) out += 'CIEN '
      else if (c === 1) out += 'CIENTO '
      else if (c === 5) out += 'QUINIENTOS '
      else if (c === 7) out += 'SETECIENTOS '
      else if (c === 9) out += 'NOVECIENTOS '
      else out += unidades[c] + 'CIENTOS '
    }

    if (resto > 10 && resto < 30) {
      out += especiales[resto] + ' '
    } else {
      if (d > 0) {
        out += decenas[d]
        if (u > 0) out += ' Y '
        else out += ' '
      }
      if (u > 0 && !(d === 2)) {
        out += unidades[u] + ' '
      }
    }
    return out.trim()
  }

  let letras = ''
  const millones = Math.floor(entero / 1000000)
  const miles = Math.floor((entero % 1000000) / 1000)
  const cientos = entero % 1000

  if (millones === 1) letras += 'UN MILLON '
  else if (millones > 1) letras += seccion(millones) + ' MILLONES '

  if (miles === 1) letras += 'MIL '
  else if (miles > 1) letras += seccion(miles) + ' MIL '

  if (cientos > 0) letras += seccion(cientos) + ' '

  return `${letras.trim()} PESOS M/CTE`
}

// Envío a impresora del navegador (abre ventana temporal de impresión 80mm)
export function imprimirHtmlTirilla(htmlContent: string) {
  const iframe = document.createElement('iframe')
  iframe.style.position = 'fixed'
  iframe.style.right = '0'
  iframe.style.bottom = '0'
  iframe.style.width = '0'
  iframe.style.height = '0'
  iframe.style.border = '0'
  document.body.appendChild(iframe)

  const doc = iframe.contentWindow?.document
  if (!doc) return

  doc.open()
  doc.write(`
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>Tirilla Mr. Burger 80mm</title>
        <style>
          @page {
            size: 80mm auto;
            margin: 0;
          }
          body {
            font-family: 'Courier New', Courier, monospace;
            font-size: 12px;
            color: #000;
            background: #fff;
            width: 72mm;
            margin: 0 auto;
            padding: 8px 4px;
            line-height: 1.25;
          }
          .center { text-align: center; }
          .right { text-align: right; }
          .bold { font-weight: bold; }
          .double { font-size: 15px; font-weight: bold; }
          .divider { border-top: 1px dashed #000; margin: 6px 0; }
          .double-divider { border-top: 2px solid #000; margin: 6px 0; }
          table { width: 100%; border-collapse: collapse; }
          td, th { padding: 2px 0; font-size: 12px; }
          .firmas-box {
            margin-top: 24px;
            display: flex;
            justify-content: space-between;
            text-align: center;
            font-size: 10px;
          }
          .firma-line {
            width: 30%;
            border-top: 1px solid #000;
            padding-top: 4px;
          }
        </style>
      </head>
      <body>
        ${htmlContent}
        <script>
          window.onload = function() {
            window.focus();
            window.print();
            setTimeout(function() {
              window.frameElement.parentNode.removeChild(window.frameElement);
            }, 1000);
          };
        </script>
      </body>
    </html>
  `)
  doc.close()
}

// Impresión directa ESC/POS mediante WebUSB (para impresoras térmicas conectadas por USB)
export async function imprimirViaWebUSB(rawBytes: Uint8Array): Promise<{ success: boolean; message: string }> {
  if (!('usb' in navigator)) {
    return {
      success: false,
      message: 'Tu navegador no soporta WebUSB. Usa el botón de impresión estándar.'
    }
  }

  try {
    const device = await (navigator as any).usb.requestDevice({
      filters: [] // Permite seleccionar cualquier dispositivo USB conectado
    })

    await device.open()
    if (device.configuration === null) {
      await device.selectConfiguration(1)
    }
    await device.claimInterface(0)

    // Buscar endpoint de salida (Out)
    const endpoint = device.configuration.interfaces[0].alternate.endpoints.find(
      (e: any) => e.direction === 'out'
    )

    if (!endpoint) {
      await device.close()
      return { success: false, message: 'No se encontró un canal de comunicación con la impresora.' }
    }

    await device.transferOut(endpoint.endpointNumber, rawBytes)
    await device.close()
    return { success: true, message: 'Impresión enviada correctamente a la impresora USB.' }
  } catch (err: any) {
    if (err.name === 'NotFoundError') {
      return { success: false, message: 'No se seleccionó ninguna impresora USB.' }
    }
    return { success: false, message: `Error WebUSB: ${err.message || 'Error de conexión'}` }
  }
}

// Convertidor de texto plano a comandos binarios ESC/POS
export function generarBytesEscPos(texto: string): Uint8Array {
  const encoder = new TextEncoder()
  const bytesTexto = encoder.encode(texto)

  // Comandos ESC/POS estándar:
  // ESC @ (Inicializar) + texto + LF + GS V A 3 (Corte de papel con avance)
  const init = new Uint8Array([0x1B, 0x40])
  const cut = new Uint8Array([0x0A, 0x0A, 0x0A, 0x1D, 0x56, 0x41, 0x03])

  const totalBytes = new Uint8Array(init.length + bytesTexto.length + cut.length)
  totalBytes.set(init, 0)
  totalBytes.set(bytesTexto, init.length)
  totalBytes.set(cut, init.length + bytesTexto.length)

  return totalBytes
}
