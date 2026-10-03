import React from 'react'

interface FooterCreditsProps {
  className?: string
  showSystem?: boolean
}

export const FooterCredits: React.FC<FooterCreditsProps> = ({ className = '', showSystem = true }) => {
  return (
    <footer className={`py-3 px-4 text-center text-xs text-slate-500 select-none ${className}`}>
      <span>Desarrollado por </span>
      <strong className="text-amber-400 font-semibold tracking-wide">Ing. Jhon Arias</strong>
      {showSystem && <span className="opacity-70 text-slate-400"> • MR. BURGER POS</span>}
    </footer>
  )
}
