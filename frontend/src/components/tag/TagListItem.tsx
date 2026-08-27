import { useState } from 'react'

import type { Tag } from '../../api/client'
import { Button } from '../Button'
import { Card } from '../Card'
import { FieldError } from '../FieldError'

interface TagListItemProps {
  tag: Tag
  /** True while this row's rename request is in flight. */
  renaming?: boolean
  onRename: (name: string) => void
  onDelete: () => void
}

/** One row on TagsPage: name, prompt_count, rename (inline edit) and
 * delete actions (FR-033, FR-034). */
export function TagListItem({ tag, renaming = false, onRename, onDelete }: TagListItemProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(tag.name)
  const [editError, setEditError] = useState<string>()

  function handleDraftChange(value: string) {
    setDraft(value)
    if (editError) setEditError(undefined)
  }

  // Enter is an explicit "commit this" signal, so an empty name here
  // blocks the commit and shows why, rather than silently discarding it -
  // mirrors backend/app/models.py's tag-name validator (non-empty after
  // trim, max 50 chars, already enforced by maxLength below).
  function commitRename() {
    const trimmed = draft.trim()
    if (!trimmed) {
      setEditError('Tag name is required.')
      return
    }
    setEditing(false)
    setEditError(undefined)
    if (trimmed !== tag.name) onRename(trimmed)
  }

  function cancelRename() {
    setDraft(tag.name)
    setEditing(false)
    setEditError(undefined)
  }

  // Blur is an incidental signal (clicking elsewhere), unlike Enter's
  // explicit commit - an empty draft here just cancels the edit instead of
  // trapping the user in the field with an error they didn't ask to see.
  function handleBlur() {
    if (!draft.trim()) {
      cancelRename()
      return
    }
    commitRename()
  }

  return (
    <Card className="flex items-center justify-between gap-3">
      {editing ? (
        <div className="min-w-0">
          <input
            autoFocus
            type="text"
            value={draft}
            maxLength={50}
            onChange={(event) => handleDraftChange(event.target.value)}
            onBlur={handleBlur}
            onKeyDown={(event) => {
              if (event.key === 'Enter') commitRename()
              else if (event.key === 'Escape') cancelRename()
            }}
            aria-invalid={Boolean(editError)}
            aria-describedby={editError ? `tag-${tag.id}-rename-error` : undefined}
            className={`w-full rounded-md border px-2 py-1 text-sm focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 ${
              editError
                ? 'border-red-400 focus:border-red-500 focus-visible:outline-red-600'
                : 'border-slate-300 focus:border-blue-500 focus-visible:outline-blue-600'
            }`}
          />
          <FieldError id={`tag-${tag.id}-rename-error`} message={editError} />
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setEditing(true)}
          disabled={renaming}
          className="min-w-0 text-left"
        >
          <span className="break-words text-sm font-semibold text-slate-900">{tag.name}</span>
          <span className="ml-2 text-xs text-slate-500">{tag.prompt_count} prompt(s)</span>
          {renaming && (
            <span
              className="ml-2 inline-block h-3 w-3 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600 align-middle"
              aria-hidden="true"
            />
          )}
        </button>
      )}
      <Button variant="danger" onClick={onDelete} disabled={renaming} className="shrink-0">
        Delete
      </Button>
    </Card>
  )
}
