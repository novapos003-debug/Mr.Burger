import React, { useState, useEffect } from 'react'
import {
  Printer,
  X,
  CheckCircle2,
  AlertCircle,
  Loader2,
  DollarSign,
  Sliders,
  Sparkles,
} from 'lucide-react'
import {
  getPrinterConfig,
  savePrinterConfig,
  imprimirTicketPrueba,
  abrirCajonMonedero,
  type ConfiguracionImpresora,
} from '../../utils/printer'

interface Props {
  isOpen: boolean
  onClose: () => void
}

export const ConfiguracionImpresoraModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const [config, setConfig] = useState<ConfiguracionImpresora>(getPrinterConfig())
  const [feedback, setFeedback] = useState<{ tipo: 'ok' | 'err'; msg: string } | null>(null)
  const [probando, setProbando] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setConfig(getPrinterConfig())
      setFeedback(null)
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleGuardar = () => {
    savePrinterConfig(config)
    setFeedback({ tipo: 'ok', msg: '✓ Configuración de impresora guardada exitosamente en esta terminal.' })
    setTimeout(() => {
      setFeedback(null)
      onClose()
    }, 1500)
  }

  const handlePruebaTicket = async () => {
    try {
      setProbando(true)
      setFeedback(null)
      const res = await imprimirTicketPrueba(config)
      setFeedback({ tipo: 'ok', msg: res.message || 'Ticket de prueba enviado a la impresora.' })
    } catch (err: any) {
      setFeedback({ tipo: 'err', msg: err?.message || 'Error al enviar ticket de prueba.' })
    } finally {
      setProbando(false)
    }
  }

  const handlePruebaCajon = async () => {
    try {
      setProbando(true)
      setFeedback(null)
      const ok = await abrirCajonMonedero()
      if (ok) {
        setFeedback({ tipo: 'ok', msg: 'Comando de apertura RJ11 enviado a la gaveta.' })
      } else {
        setFeedback({
          tipo: 'err',
          msg: 'Para abrir por comando directo se requiere WebUSB. Si tu impresora está instalada en Windows, configura la apertura automática en las Propiedades del Driver de Windows.',
        })
      }
    } catch (err: any) {
      setFeedback({ tipo: 'err', msg: err?.message || 'Error enviando pulso a la gaveta.' })
    } finally {
      setProbando(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-3 sm:p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Cabecera */}
        <div className="p-4 border-b border-slate-800 bg-slate-800/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500/20 border border-sky-500/40 flex items-center justify-center text-sky-400">
              <Printer className="w-6 h-6" />
            </div>
            <div>
              <h2 className="font-black text-white text-base tracking-wide flex items-center gap-2">
                <span>Configuración de Impresora & Gaveta</span>
              </h2>
              <p className="text-xs text-slate-400">
                Ajuste de formato térmico, tirillas y apertura de caja registradora
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Mensaje de feedback */}
        {feedback && (
          <div
            className={`p-3 text-xs flex items-center gap-2 border-b ${
              feedback.tipo === 'ok'
                ? 'bg-emerald-950/80 border-emerald-800 text-emerald-200'
                : 'bg-rose-950/80 border-rose-800 text-rose-200'
            }`}
          >
            {feedback.tipo === 'ok' ? (
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            )}
            <span>{feedback.msg}</span>
          </div>
        )}

        {/* Contenido / Opciones */}
        <div className="p-5 overflow-y-auto space-y-5 text-xs text-slate-300">
          {/* 1. Ancho de Papel Térmico */}
          <div className="space-y-2">
            <label className="font-bold text-white uppercase tracking-wider block flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-amber-400" />
              <span>Ancho de Papel Térmico (Rollo)</span>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setConfig((prev) => ({ ...prev, tamanoPapel: '80mm' }))}
                className={`p-3.5 rounded-2xl border text-left transition cursor-pointer ${
                  config.tamanoPapel === '80mm'
                    ? 'bg-sky-950/60 border-sky-500 text-white shadow-md ring-1 ring-sky-500'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-white'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-black text-sm text-sky-400">80 mm (Estándar POS)</span>
                  {config.tamanoPapel === '80mm' && <CheckCircle2 className="w-4 h-4 text-sky-400" />}
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Impresoras térmicas de restaurante (48 columnas, Epson, Xprinter 80, Bixolon, 3nStar).
                </p>
              </button>

              <button
                type="button"
                onClick={() => setConfig((prev) => ({ ...prev, tamanoPapel: '58mm' }))}
                className={`p-3.5 rounded-2xl border text-left transition cursor-pointer ${
                  config.tamanoPapel === '58mm'
                    ? 'bg-sky-950/60 border-sky-500 text-white shadow-md ring-1 ring-sky-500'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-white'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-black text-sm text-sky-400">58 mm (Mini / Portátil)</span>
                  {config.tamanoPapel === '58mm' && <CheckCircle2 className="w-4 h-4 text-sky-400" />}
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Impresoras compactas de 2 pulgadas (32 columnas, mini bluetooth o USB portátil).
                </p>
              </button>
            </div>
          </div>

          {/* 2. Método de Impresión */}
          <div className="space-y-2">
            <label className="font-bold text-white uppercase tracking-wider block flex items-center gap-1.5">
              <Printer className="w-3.5 h-3.5 text-emerald-400" />
              <span>Método de Envío a la Impresora</span>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setConfig((prev) => ({ ...prev, modoImpresion: 'NAVEGADOR' }))}
                className={`p-3.5 rounded-2xl border text-left transition cursor-pointer ${
                  config.modoImpresion === 'NAVEGADOR'
                    ? 'bg-emerald-950/50 border-emerald-500 text-white shadow-md ring-1 ring-emerald-500'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-white'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-black text-sm text-emerald-400">Navegador Windows (Recomendado)</span>
                  {config.modoImpresion === 'NAVEGADOR' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Universal: funciona con cualquier impresora conectada por USB, Wi-Fi o Red en Windows sin configurar puertos.
                </p>
              </button>

              <button
                type="button"
                onClick={() => setConfig((prev) => ({ ...prev, modoImpresion: 'WEBUSB' }))}
                className={`p-3.5 rounded-2xl border text-left transition cursor-pointer ${
                  config.modoImpresion === 'WEBUSB'
                    ? 'bg-purple-950/50 border-purple-500 text-white shadow-md ring-1 ring-purple-500'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-white'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-black text-sm text-purple-400">WebUSB / ESC-POS Directo</span>
                  {config.modoImpresion === 'WEBUSB' && <CheckCircle2 className="w-4 h-4 text-purple-400" />}
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Envío directo binario por USB (corte automático sin ventana previa). Requiere permiso USB en Chrome/Edge.
                </p>
              </button>
            </div>
          </div>

          {/* 3. Opciones Automáticas */}
          <div className="space-y-3 bg-slate-950/80 p-4 rounded-2xl border border-slate-800">
            <h3 className="font-bold text-white uppercase tracking-wider text-[11px] text-slate-400">
              Automatizaciones al Cobrar
            </h3>

            <label className="flex items-center justify-between gap-3 cursor-pointer p-2 rounded-xl hover:bg-slate-900 transition">
              <div>
                <span className="font-bold text-white block">Abrir Gaveta de Dinero (RJ11) al cobrar</span>
                <span className="text-[11px] text-slate-400">
                  Patea el cajón monedero automáticamente cuando se registre un pago en efectivo.
                </span>
              </div>
              <input
                type="checkbox"
                checked={config.abrirCajonEfectivo}
                onChange={(e) => setConfig((prev) => ({ ...prev, abrirCajonEfectivo: e.target.checked }))}
                className="w-5 h-5 accent-emerald-500 rounded cursor-pointer"
              >
              </input>
            </label>

            <label className="flex items-center justify-between gap-3 cursor-pointer p-2 rounded-xl hover:bg-slate-900 transition">
              <div>
                <span className="font-bold text-white block">Imprimir Tirilla de Venta automáticamente</span>
                <span className="text-[11px] text-slate-400">
                  Abre la tirilla de pago tan pronto se finalice el cobro de la orden.
                </span>
              </div>
              <input
                type="checkbox"
                checked={config.autoImprimirCobro}
                onChange={(e) => setConfig((prev) => ({ ...prev, autoImprimirCobro: e.target.checked }))}
                className="w-5 h-5 accent-emerald-500 rounded cursor-pointer"
              >
              </input>
            </label>
          </div>

          {/* 4. Pruebas Rápidas de Diagnóstico */}
          <div className="p-4 bg-slate-800/40 rounded-2xl border border-slate-700/80 space-y-3">
            <span className="font-black text-xs text-white block flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span>Pruebas de Diagnóstico en Tiempo Real</span>
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <button
                type="button"
                onClick={handlePruebaTicket}
                disabled={probando}
                className="flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-bold transition cursor-pointer disabled:opacity-50"
              >
                {probando ? <Loader2 className="w-4 h-4 animate-spin text-sky-400" /> : <Printer className="w-4 h-4 text-sky-400" />}
                <span>Imprimir Ticket de Prueba</span>
              </button>

              <button
                type="button"
                onClick={handlePruebaCajon}
                disabled={probando}
                className="flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-bold transition cursor-pointer disabled:opacity-50"
              >
                {probando ? <Loader2 className="w-4 h-4 animate-spin text-emerald-400" /> : <DollarSign className="w-4 h-4 text-emerald-400" />}
                <span>Probar Apertura Gaveta RJ11</span>
              </button>
            </div>
            <p className="text-[10px] text-slate-400 italic">
              Tip Windows: Si usas la impresora por Windows y tienes gaveta RJ11, abre &quot;Dispositivos e impresoras&quot; &gt; &quot;Propiedades de la impresora&quot; &gt; pestaña &quot;Configuración de dispositivo&quot; y activa &quot;Cajón de dinero: Abrir antes de imprimir&quot;.
            </p>
          </div>
        </div>

        {/* Pie de modal */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/80 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white transition cursor-pointer"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleGuardar}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-black bg-sky-600 hover:bg-sky-500 text-white shadow-lg transition cursor-pointer"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Guardar Configuración</span>
          </button>
        </div>
      </div>
    </div>
  )
}
