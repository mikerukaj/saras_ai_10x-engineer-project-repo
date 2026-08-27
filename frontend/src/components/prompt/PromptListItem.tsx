import { Link } from 'react-router-dom'

import type { Prompt } from '../../api/client'
import { Card } from '../Card'
import { TagBadge } from '../tag/TagBadge'

interface PromptListItemProps {
  prompt: Prompt
  // Resolved from prompt.collection_id by the caller (which already has
  // the full collection list loaded) - keeps this component's own props
  // limited to what it renders, per specs/frontend.md's component
  // inventory, without re-fetching collections per row.
  collectionName?: string
}

/** One row in the prompt list: title, description, collection badge, tag
 * badges, link to detail (FR-001). */
export function PromptListItem({ prompt, collectionName }: PromptListItemProps) {
  return (
    <Card>
      <Link to={`/prompts/${prompt.id}`} className="block">
        <h2 className="break-words text-sm font-semibold text-slate-900 hover:underline">{prompt.title}</h2>
        {prompt.description && <p className="mt-1 break-words text-sm text-slate-600">{prompt.description}</p>}
      </Link>
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <span className="max-w-[12rem] truncate rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
          {collectionName ?? 'No collection'}
        </span>
        {prompt.tags.map((tag) => (
          <TagBadge key={tag.id} tag={tag} />
        ))}
      </div>
    </Card>
  )
}
