import { useState } from 'react'

import type { Tag } from '../../api/client'
import { Button } from '../Button'
import { Card } from '../Card'

interface TagListItemProps {
  tag: Tag
  onRename: (name: string) => void
  onDelete: () => void
}

/** One row on TagsPage: name, prompt_count, rename (inline edit) and
 * delete actions (FR-033, FR-034). */
export function TagListItem({ tag, onRename, onDelete }: TagListItemProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(tag.name)

  function commitRename() {
    setEditing(false)
    if (draft.trim() && draft.trim() !== tag.name) onRename(draft.trim())
    else setDraft(tag.name)
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
          onKeyDown={(event) => event.key === 'Enter' && commitRename()}
          className="rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none"
        />
      ) : (
        <button type="button" onClick={() => setEditing(true)} className="text-left">
          <span className="text-sm font-semibold text-slate-900">{tag.name}</span>
          <span className="ml-2 text-xs text-slate-500">{tag.prompt_count} prompt(s)</span>
        </button>
      )}
      <Button variant="danger" onClick={onDelete}>
        Delete
      </Button>
    </Card>
  )
}
