import { Button } from './Button'

interface EmptyStateProps {
  message: string
  action?: { label: string; onClick: () => void }
}

/** Generic "nothing here yet" placeholder, distinct from an error — used
 * for empty lists (e.g. no prompts yet vs. no prompts match a filter). */
export function EmptyState({ message, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-slate-300 py-12 text-center">
      <p className="text-sm text-slate-500">{message}</p>
      {action && <Button onClick={action.onClick}>{action.label}</Button>}
    </div>
  )
}
