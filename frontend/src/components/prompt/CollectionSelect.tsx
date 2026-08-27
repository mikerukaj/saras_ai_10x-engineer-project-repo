import type { Collection } from '../../api/client'

interface CollectionSelectProps {
  collections: Collection[]
  value: string | null
  onChange: (id: string | null) => void
}

/** Dropdown for choosing a prompt's collection (including "No
 * collection"). Used inside PromptForm and PromptFilters. */
export function CollectionSelect({ collections, value, onChange }: CollectionSelectProps) {
  return (
    <select
      value={value ?? ''}
      onChange={(event) => onChange(event.target.value || null)}
      className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-blue-600"
    >
      <option value="">No collection</option>
      {collections.map((collection) => (
        <option key={collection.id} value={collection.id}>
          {collection.name}
        </option>
      ))}
    </select>
  )
}
