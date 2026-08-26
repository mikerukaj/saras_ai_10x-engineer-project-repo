import type { ReactNode } from 'react'

import { NavBar } from './NavBar'

interface AppShellProps {
  children: ReactNode
}

/** Top-level layout: nav bar + main content slot. Every page renders
 * inside it via the router's layout route (see App.tsx). */
export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-slate-50">
      <NavBar />
      <main>{children}</main>
    </div>
  )
}
