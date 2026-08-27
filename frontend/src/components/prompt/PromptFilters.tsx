import type { Collection, Tag } from '../../api/client'

export interface PromptFilterState {
  search: string
  collectionId?: string
  tagNames: string[]
}

interface PromptFiltersProps {
  collections: Collection[]
  tags: Tag[]
  value: PromptFilterState
  onChange: (next: PromptFilterState) => void
}

/** Search input + collection filter dropdown + tag filter, synced to URL
 * search params by the caller (PromptListPage) so filtered views are
 * bookmarkable/shareable (FR-002, FR-032). */
export function PromptFilters({ collections, tags, value, onChange }: PromptFiltersProps) {
  function toggleTag(name: string) {
    const active = value.tagNames.includes(name)
    onChange({
      ...value,
      tagNames: active ? value.tagNames.filter((t) => t !== name) : [...value.tagNames, name],
    })
  }

  return (
    <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center">
      <input
        type="search"
        value={value.search}
        onChange={(event) => onChange({ ...value, search: event.target.value })}
        placeholder="Search prompts…"
        aria-label="Search prompts"
        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none sm:max-w-xs"
      />

      <select
        value={value.collectionId ?? ''}
        onChange={(event) => onChange({ ...value, collectionId: event.target.value || undefined })}
        aria-label="Filter by collection"
        className="rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
      >
        <option value="">All collections</option>
        {collections.map((collection) => (
          <option key={collection.id} value={collection.id}>
            {collection.name}
          </option>
        ))}
      </select>

      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {tags.map((tag) => {
            const active = value.tagNames.includes(tag.name)
            return (
              <button
                key={tag.id}
                type="button"
                onClick={() => toggleTag(tag.name)}
                className={`max-w-[10rem] truncate rounded-full px-2 py-0.5 text-xs font-medium ${
                  active ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {tag.name}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
