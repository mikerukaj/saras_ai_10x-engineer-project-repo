import { Button } from './Button'

interface ConfirmDialogProps {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  /** True while the confirmed action's request is in flight — keeps the
   * dialog open with a spinner on Confirm instead of closing immediately,
   * so a slow network doesn't look like the click did nothing. Callers
   * close the dialog themselves once the mutation settles. */
  confirming?: boolean
  onConfirm: () => void
  onCancel: () => void
}

/** Reusable confirmation modal for every destructive action (delete
 * prompt, delete collection, delete version, delete tag, restore version)
 * — a single implementation instead of five ad hoc confirms, per FR-006's
 * "explicit confirmation step". */
export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  confirming = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
    >
      <div className="w-full max-w-sm rounded-lg bg-white p-5 shadow-lg">
        <h2 id="confirm-dialog-title" className="text-base font-semibold text-slate-900">
          {title}
        </h2>
        <p className="mt-2 text-sm text-slate-600">{message}</p>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="secondary" disabled={confirming} onClick={onCancel}>
            Cancel
          </Button>
          <Button variant="danger" loading={confirming} onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
