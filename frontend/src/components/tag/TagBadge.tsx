import type { Tag } from '../../api/client'

interface TagBadgeProps {
  tag: Tag
  onRemove?: () => void
}

/** Small chip rendering one tag's name, used on PromptListItem and
 * PromptDetailPage. */
export function TagBadge({ tag, onRemove }: TagBadgeProps) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
      {tag.name}
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Remove tag ${tag.name}`}
          className="rounded-full text-slate-400 hover:text-slate-700"
        >
          ×
        </button>
      )}
    </span>
  )
}
