// Generador de sonidos del KDS usando Web Audio API nativo (sin dependencias externas ni archivos pesados)

let audioCtx: AudioContext | null = null

function getAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
    if (AudioContextClass) {
      audioCtx = new AudioContextClass()
    }
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume()
  }
  return audioCtx
}

export function isSoundMuted(): boolean {
  if (typeof window === 'undefined') return false
  return localStorage.getItem('kds_sound_muted') === 'true'
}

export function setSoundMuted(muted: boolean): void {
  if (typeof window === 'undefined') return
  localStorage.setItem('kds_sound_muted', muted ? 'true' : 'false')
}

/**
 * Campanilla de cocina suave y clara para nuevas comandas entrantes (Ding-Dong)
 */
export function playNewOrderChime(): void {
  if (isSoundMuted()) return
  try {
    const ctx = getAudioContext()
    if (!ctx) return

    const now = ctx.currentTime

    // Tono 1 (Ding)
    const osc1 = ctx.createOscillator()
    const gain1 = ctx.createGain()
    osc1.type = 'sine'
    osc1.frequency.setValueAtTime(587.33, now) // D5
    gain1.gain.setValueAtTime(0.3, now)
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.45)
    osc1.connect(gain1)
    gain1.connect(ctx.destination)
    osc1.start(now)
    osc1.stop(now + 0.45)

    // Tono 2 (Dong)
    const osc2 = ctx.createOscillator()
    const gain2 = ctx.createGain()
    osc2.type = 'sine'
    osc2.frequency.setValueAtTime(880.0, now + 0.15) // A5
    gain2.gain.setValueAtTime(0.35, now + 0.15)
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.8)
    osc2.connect(gain2)
    gain2.connect(ctx.destination)
    osc2.start(now + 0.15)
    osc2.stop(now + 0.8)
  } catch (err) {
    console.warn('AudioContext play error:', err)
  }
}

/**
 * Alerta urgente para pedidos demorados o tiempo crítico excedido
 */
export function playAlertChime(): void {
  if (isSoundMuted()) return
  try {
    const ctx = getAudioContext()
    if (!ctx) return

    const now = ctx.currentTime
    for (let i = 0; i < 3; i++) {
      const startTime = now + i * 0.18
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'triangle'
      osc.frequency.setValueAtTime(440.0, startTime) // A4
      gain.gain.setValueAtTime(0.25, startTime)
      gain.gain.exponentialRampToValueAtTime(0.001, startTime + 0.14)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(startTime)
      osc.stop(startTime + 0.14)
    }
  } catch (err) {
    console.warn('AudioContext alert error:', err)
  }
}
