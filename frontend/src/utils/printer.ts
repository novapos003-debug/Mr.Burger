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
  recargo_empaque?: number
  tipo_consumo?: string
  total: number
  pagos: Array<{
    metodo: string
    monto: number
    recibido?: number
    cambio?: number
    referencia?: string
  }>
  cajero?: string
  // Cuenta que el cliente pide antes de pagar: sin pagos y marcada como pendiente
  esPrecuenta?: boolean
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

export interface ConfiguracionImpresora {
  tamanoPapel: '58mm' | '80mm'
  modoImpresion: 'NAVEGADOR' | 'WEBUSB'
  abrirCajonEfectivo: boolean
  autoImprimirCobro: boolean
}

export const CONFIG_IMPRESORA_DEFAULT: ConfiguracionImpresora = {
  tamanoPapel: '80mm',
  modoImpresion: 'NAVEGADOR',
  abrirCajonEfectivo: true,
  autoImprimirCobro: true,
}

export function getPrinterConfig(): ConfiguracionImpresora {
  try {
    const raw = localStorage.getItem('mrburger_printer_config')
    if (raw) {
      const parsed = JSON.parse(raw)
      return { ...CONFIG_IMPRESORA_DEFAULT, ...parsed }
    }
  } catch {
    // fallback
  }
  return CONFIG_IMPRESORA_DEFAULT
}

export function savePrinterConfig(cfg: ConfiguracionImpresora): void {
  try {
    localStorage.setItem('mrburger_printer_config', JSON.stringify(cfg))
  } catch (err) {
    console.error('Error guardando configuración de impresora:', err)
  }
}

// Envío a impresora del navegador (soporta 58mm y 80mm continuo)
export function imprimirHtmlTirilla(htmlContent: string, tamanoPapel?: '58mm' | '80mm') {
  const config = getPrinterConfig()
  const papel = tamanoPapel || config.tamanoPapel || '80mm'
  const is58 = papel === '58mm'

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
        <title>Tirilla Mr. Burger ${papel}</title>
        <style>
          @page {
            size: ${is58 ? '58mm' : '80mm'} auto;
            margin: 0;
          }
          body {
            font-family: 'Courier New', Courier, monospace;
            font-size: ${is58 ? '10px' : '12px'};
            color: #000;
            background: #fff;
            width: ${is58 ? '48mm' : '72mm'};
            margin: 0 auto;
            padding: ${is58 ? '4px 2px' : '8px 4px'};
            line-height: 1.25;
            word-wrap: break-word;
          }
          .center { text-align: center; }
          .right { text-align: right; }
          .bold { font-weight: bold; }
          .double { font-size: ${is58 ? '12px' : '15px'}; font-weight: bold; }
          .divider { border-top: 1px dashed #000; margin: ${is58 ? '4px 0' : '6px 0'}; }
          .double-divider { border-top: 2px solid #000; margin: ${is58 ? '4px 0' : '6px 0'}; }
          table { width: 100%; border-collapse: collapse; }
          td, th { padding: 1px 0; font-size: ${is58 ? '10px' : '12px'}; }
          .firmas-box {
            margin-top: 20px;
            display: flex;
            justify-content: space-between;
            text-align: center;
            font-size: ${is58 ? '8px' : '10px'};
          }
          .firma-line {
            width: 38%;
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
              window.frameElement?.parentNode?.removeChild(window.frameElement);
            }, 1000);
          };
        </script>
      </body>
    </html>
  `)
  doc.close()
}

export async function imprimirTicketPrueba(cfg?: ConfiguracionImpresora): Promise<{ success: boolean; message: string }> {
  const config = cfg || getPrinterConfig()
  const fechaStr = new Date().toLocaleString('es-CO')
  const papel = config.tamanoPapel || '80mm'
  const is58 = papel === '58mm'

  if (config.modoImpresion === 'WEBUSB') {
    const textoEsc = `
================================
           MR. BURGER           
     PRUEBA DE IMPRESORA POS    
       Formato: ${papel}       
  ${fechaStr}
--------------------------------
    [OK] IMPRESORA TERMICA      
   COMUNICACION ESC/POS DIRECTA 
--------------------------------
 Gaveta RJ11: ${config.abrirCajonEfectivo ? 'Habilitada' : 'No'}
 Auto-Ticket: ${config.autoImprimirCobro ? 'Habilitado' : 'No'}
--------------------------------
  ¡IMPRESORA LISTA PARA CAJA!   
================================
`
    return imprimirTirillaTermica(textoEsc)
  }

  const html = `
    <div class="center bold double">MR. BURGER</div>
    <div class="center bold">PRUEBA DE IMPRESORA POS</div>
    <div class="center" style="font-size: ${is58 ? '9px' : '11px'};">Formato: ${papel}</div>
    <div class="center" style="font-size: ${is58 ? '9px' : '11px'};">${fechaStr}</div>
    <div class="divider"></div>
    <div class="center bold">✓ IMPRESORA CONFIGURADA</div>
    <div class="divider"></div>
    <div style="font-size: ${is58 ? '9px' : '11px'};">
      <div>Método: Navegador Windows</div>
      <div>Gaveta RJ11: ${config.abrirCajonEfectivo ? 'Habilitada' : 'Deshabilitada'}</div>
      <div>Auto-Imprimir: ${config.autoImprimirCobro ? 'Habilitado' : 'Deshabilitado'}</div>
    </div>
    <div class="divider"></div>
    <div class="center bold" style="font-size: ${is58 ? '9px' : '11px'};">¡Mr. Burger listo para operar!</div>
    <br/>
  `
  imprimirHtmlTirilla(html, papel)
  return { success: true, message: 'Ticket de prueba enviado al diálogo de impresión.' }
}

// Impresión por la caja: el servidor local entrega la tirilla a la cola de Windows, que sí
// puede escribir en la impresora aunque su controlador la tenga tomada.
export async function imprimirEnCaja(texto: string, abrirCajon = false): Promise<{ success: boolean; message: string }> {
  try {
    const api = (await import('../api/client')).default
    const res = await api.post('/caja/imprimir', { texto, abrir_cajon: abrirCajon })
    return { success: Boolean(res.data?.ok), message: res.data?.mensaje || '' }
  } catch {
    return { success: false, message: 'No se pudo contactar la caja para imprimir.' }
  }
}

// Impresión térmica directa: primero por la caja y, si no tiene impresora (web o celular), por WebUSB
// Con abrirCajon, la misma orden de impresión abre también el cajón monedero.
export async function imprimirTirillaTermica(texto: string, abrirCajon = false): Promise<{ success: boolean; message: string }> {
  const porCaja = await imprimirEnCaja(texto, abrirCajon)
  if (porCaja.success) return porCaja
  const bytes = generarBytesEscPos(texto)
  if (!abrirCajon) return imprimirViaWebUSB(bytes)
  // ESC p 0 25 250 (abrir cajón vía RJ11) antes de la tirilla
  const pulso = new Uint8Array([0x1B, 0x70, 0x00, 0x19, 0xFA])
  const conCajon = new Uint8Array(pulso.length + bytes.length)
  conCajon.set(pulso, 0)
  conCajon.set(bytes, pulso.length)
  return imprimirViaWebUSB(conCajon)
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
      filters: [{ classCode: 7 }] // Clase 7 = Impresora
    })

    await device.open()
    if (device.configuration === null) {
      await device.selectConfiguration(1)
    }
    
    // Auto-claim the first available interface
    const iface = device.configuration.interfaces[0]
    await device.claimInterface(iface.interfaceNumber)

    // Buscar endpoint de salida (Out)
    const endpoint = iface.alternate.endpoints.find(
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
    if (err.name === 'SecurityError' || String(err.message).toLowerCase().includes('access denied')) {
      return {
        success: false,
        message: 'Acceso USB bloqueado por Windows: El controlador de Windows (driver) ya tiene el control exclusivo de la impresora. Usa el modo de impresión "NAVEGADOR" o configura la apertura del cajón en las Propiedades de la Impresora de Windows.',
      }
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

export async function abrirCajonMonedero(): Promise<boolean> {
  // 1. Intentar primero a través de la API local de Windows (winspool directo a la impresora térmica)
  try {
    const api = (await import('../api/client')).default
    const res = await api.post('/caja/abrir-cajon')
    if (res.data?.ok) {
      return true
    }
  } catch {
    // Si la API falla (ej. sin red local), continuar silenciosamente al siguiente intento
  }

  // 2. Intentar WebUSB si está soportado en navegadores compatibles (Android / Linux / Windows con WinUSB)
  if (!('usb' in navigator)) return false

  try {
    const device = await (navigator as any).usb.requestDevice({
      filters: [{ classCode: 7 }]
    })

    await device.open()
    if (device.configuration === null) {
      await device.selectConfiguration(1)
    }
    
    const iface = device.configuration.interfaces[0]
    await device.claimInterface(iface.interfaceNumber)

    const endpoint = iface.alternate.endpoints.find(
      (e: any) => e.direction === 'out'
    )

    if (!endpoint) {
      await device.close()
      return false
    }

    // Comando ESC p 0 25 250 (abrir cajón vía RJ11)
    const cmd = new Uint8Array([0x1B, 0x70, 0x00, 0x19, 0xFA])
    await device.transferOut(endpoint.endpointNumber, cmd)
    await device.close()
    return true
  } catch (err: any) {
    // En Windows con driver instalado, WebUSB arroja Access Denied. No alertar error intrusivo
    console.warn('Aviso al intentar WebUSB para apertura de gaveta:', err?.message || err)
    return false
  }
}

