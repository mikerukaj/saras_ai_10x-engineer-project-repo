import { useState } from 'react'

import { useCreateVersion, useDeleteVersion, usePromptVersions, useRestoreVersion } from '../../api/hooks'
import { Button } from '../Button'
import { ConfirmDialog } from '../ConfirmDialog'
import { ErrorMessageFromError } from '../ErrorMessage'
import { LoadingIndicator } from '../LoadingIndicator'
import { VersionDetailView } from './VersionDetailView'
import { VersionListItem } from './VersionListItem'

interface VersionHistoryPanelProps {
  promptId: string
}

type PendingAction = { kind: 'restore' | 'delete'; versionId: string } | null

/** Lists a prompt's versions newest-first; hosts the "save checkpoint"
 * action; opens VersionDetailView for a selected version (FR-027-030). */
export function VersionHistoryPanel({ promptId }: VersionHistoryPanelProps) {
  const { data: versions, isLoading, error } = usePromptVersions(promptId)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [pending, setPending] = useState<PendingAction>(null)
  const [checkpointLabel, setCheckpointLabel] = useState('')

  const createVersion = useCreateVersion(promptId)
  const restoreVersion = useRestoreVersion(promptId)
  const deleteVersion = useDeleteVersion(promptId)

  if (isLoading) return <LoadingIndicator label="Loading version history…" />
  if (error) return <ErrorMessageFromError error={error} />

  const sorted = [...(versions ?? [])].sort((a, b) => b.version_number - a.version_number)
  const selected = sorted.find((v) => v.id === selectedId) ?? null

  function handleSaveCheckpoint() {
    createVersion.mutate(checkpointLabel || undefined, {
      onSuccess: () => setCheckpointLabel(''),
    })
  }

  function handleConfirmPending() {
    if (!pending) return
    const { kind, versionId } = pending
    if (kind === 'restore') {
      restoreVersion.mutate(versionId, { onSettled: () => setPending(null) })
    } else {
      deleteVersion.mutate(versionId, {
        onSuccess: () => {
          if (versionId === selectedId) setSelectedId(null)
        },
        onSettled: () => setPending(null),
      })
    }
  }

  return (
    <div>
      {createVersion.error && <ErrorMessageFromError error={createVersion.error} />}
      {restoreVersion.error && <ErrorMessageFromError error={restoreVersion.error} />}
      {deleteVersion.error && <ErrorMessageFromError error={deleteVersion.error} />}

      <div className="mb-3 flex gap-2">
        <input
          type="text"
          value={checkpointLabel}
          onChange={(event) => setCheckpointLabel(event.target.value)}
          placeholder="Checkpoint label (optional)"
          maxLength={100}
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <Button variant="secondary" onClick={handleSaveCheckpoint} loading={createVersion.isPending}>
          Save checkpoint
        </Button>
      </div>

      {selected ? (
        <VersionDetailView
          version={selected}
          onRestore={() => setPending({ kind: 'restore', versionId: selected.id })}
          onDelete={() => setPending({ kind: 'delete', versionId: selected.id })}
          onClose={() => setSelectedId(null)}
        />
      ) : (
        <ul className="divide-y divide-slate-100 rounded-md border border-slate-200">
          {sorted.map((version) => (
            <VersionListItem key={version.id} version={version} onView={() => setSelectedId(version.id)} />
          ))}
        </ul>
      )}

      <ConfirmDialog
        open={pending?.kind === 'restore'}
        title="Restore this version?"
        message="The prompt's current title, content, and description will be replaced. Its current state will itself be saved as a new version first, so this can be undone."
        confirmLabel="Restore"
        confirming={restoreVersion.isPending}
        onCancel={() => setPending(null)}
        onConfirm={handleConfirmPending}
      />
      <ConfirmDialog
        open={pending?.kind === 'delete'}
        title="Delete this version?"
        message="This history entry will be permanently removed. The prompt's current state is unaffected."
        confirmLabel="Delete"
        confirming={deleteVersion.isPending}
        onCancel={() => setPending(null)}
        onConfirm={handleConfirmPending}
      />
    </div>
  )
}
