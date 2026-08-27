import { useState, type KeyboardEvent } from 'react'

import type { Tag } from '../../api/client'

interface TagInputProps {
  value: string[]
  onChange: (tags: string[]) => void
  suggestions: Tag[]
}

/** Type-to-create-or-select multi-tag input used in the create and edit
 * prompt forms (FR-031). Tag names are resolved server-side via
 * case-insensitive get-or-create, so this component only deals in plain
 * strings, not Tag records. */
export function TagInput({ value, onChange, suggestions }: TagInputProps) {
  const [draft, setDraft] = useState('')

  function addTag(name: string) {
    const trimmed = name.trim()
    if (!trimmed) return
    const alreadyPresent = value.some((existing) => existing.toLowerCase() === trimmed.toLowerCase())
    if (!alreadyPresent) onChange([...value, trimmed])
    setDraft('')
  }

  function removeTag(name: string) {
    onChange(value.filter((existing) => existing !== name))
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault()
      addTag(draft)
    } else if (event.key === 'Backspace' && draft === '' && value.length > 0) {
      removeTag(value[value.length - 1])
    }
  }

  const matchingSuggestions = suggestions
    .filter((tag) => tag.name.toLowerCase().includes(draft.toLowerCase()))
    .filter((tag) => !value.some((existing) => existing.toLowerCase() === tag.name.toLowerCase()))
    .slice(0, 5)

  return (
    <div>
      <div className="flex flex-wrap items-center gap-1.5 rounded-md border border-slate-300 p-2 focus-within:border-blue-500">
        {value.map((name) => (
          <span
            key={name}
            className="inline-flex max-w-[10rem] items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700"
          >
            <span className="truncate">{name}</span>
            <button
              type="button"
              onClick={() => removeTag(name)}
              aria-label={`Remove tag ${name}`}
              className="text-slate-400 hover:text-slate-700"
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => addTag(draft)}
          placeholder={value.length === 0 ? 'Add tags…' : ''}
          className="min-w-[8ch] flex-1 border-none text-sm outline-none"
        />
      </div>
      {draft && matchingSuggestions.length > 0 && (
        <ul className="mt-1 rounded-md border border-slate-200 bg-white text-sm shadow-sm">
          {matchingSuggestions.map((tag) => (
            <li key={tag.id}>
              <button
                type="button"
                onClick={() => addTag(tag.name)}
                className="block w-full break-words px-3 py-1.5 text-left hover:bg-slate-50"
              >
                {tag.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
