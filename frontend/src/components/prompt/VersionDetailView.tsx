import type { PromptVersion } from '../../api/client'
import { Button } from '../Button'
import { PromptContent } from './PromptContent'

interface VersionDetailViewProps {
  version: PromptVersion
  onRestore: () => void
  onDelete: () => void
  onClose: () => void
}

/** Shows one past version's full title/content/description; hosts
 * restore and delete actions (FR-027, FR-028, FR-030). Confirmation for
 * both actions is the caller's responsibility (ConfirmDialog). */
export function VersionDetailView({ version, onRestore, onDelete, onClose }: VersionDetailViewProps) {
  return (
    <div className="rounded-md border border-slate-200 p-4">
      <div className="flex items-start justify-between gap-3">
        <h3 className="min-w-0 break-words text-sm font-semibold text-slate-900">
          Version {version.version_number}
          {version.label && <span className="ml-2 font-normal text-slate-500">— {version.label}</span>}
        </h3>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="shrink-0 text-slate-400 hover:text-slate-700"
        >
          ×
        </button>
      </div>
      <p className="mt-2 break-words text-sm font-medium text-slate-800">{version.title}</p>
      {version.description && <p className="mt-1 break-words text-sm text-slate-600">{version.description}</p>}
      <div className="mt-2">
        <PromptContent content={version.content} />
      </div>
      <div className="mt-4 flex gap-2">
        <Button onClick={onRestore}>Restore this version</Button>
        <Button variant="danger" onClick={onDelete}>
          Delete version
        </Button>
      </div>
    </div>
  )
}
