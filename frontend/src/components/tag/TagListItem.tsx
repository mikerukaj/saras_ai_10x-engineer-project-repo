import { useState } from 'react'

import type { Tag } from '../../api/client'
import { Button } from '../Button'
import { Card } from '../Card'

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

  function commitRename() {
    setEditing(false)
    if (draft.trim() && draft.trim() !== tag.name) onRename(draft.trim())
    else setDraft(tag.name)
  }

  function cancelRename() {
    // Reset the draft first so the onBlur this triggers (via the input
    // unmounting) sees draft === tag.name and no-ops instead of
    // re-committing whatever was typed.
    setDraft(tag.name)
    setEditing(false)
  }

  return (
    <Card className="flex items-center justify-between gap-3">
      {editing ? (
        <input
          autoFocus
          type="text"
          value={draft}
          maxLength={50}
          onChange={(event) => setDraft(event.target.value)}
          onBlur={commitRename}
          onKeyDown={(event) => {
            if (event.key === 'Enter') commitRename()
            else if (event.key === 'Escape') cancelRename()
          }}
          className="rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-blue-600"
        />
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
