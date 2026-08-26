import type { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
}

/** Bordered/padded container used for list rows, form sections, and panels. */
export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`rounded-lg border border-slate-200 bg-white p-4 shadow-sm ${className}`}>
      {children}
    </div>
  )
}
