import type { ReactNode } from 'react'

interface PageProps {
  title: string
  actions?: ReactNode
  children: ReactNode
}

/** Per-screen wrapper: page title, consistent padding/max-width. The one
 * place page-level spacing/typography is defined, so every screen looks
 * consistent (FR-025). Responsive: no horizontal scroll at 375px (FR-024). */
export function Page({ title, actions, children }: PageProps) {
  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-6 sm:px-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="min-w-0 break-words text-xl font-semibold text-slate-900 sm:text-2xl">{title}</h1>
        {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
      </div>
      {children}
    </div>
  )
}
