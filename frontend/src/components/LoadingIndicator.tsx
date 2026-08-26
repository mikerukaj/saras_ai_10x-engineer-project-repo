interface LoadingIndicatorProps {
  label?: string
}

/** Visible loading spinner/state (FR-023) — shown for any action waiting
 * on a backend response so the interface never appears frozen. */
export function LoadingIndicator({ label = 'Loading…' }: LoadingIndicatorProps) {
  return (
    <div className="flex items-center gap-2 py-8 text-sm text-slate-500" role="status">
      <span
        className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600"
        aria-hidden="true"
      />
      {label}
    </div>
  )
}
