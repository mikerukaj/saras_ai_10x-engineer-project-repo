import { useState, type FormEvent } from 'react'

import { useCollections, useTags } from '../../api/hooks'
import type { PromptCreate } from '../../api/client'
import { Button } from '../Button'
import { ErrorMessageFromError } from '../ErrorMessage'
import { FieldError } from '../FieldError'
import { TagInput } from '../tag/TagInput'
import { CollectionSelect } from './CollectionSelect'

interface PromptFormProps {
  initialValue?: Partial<PromptCreate>
  submitLabel: string
  onSubmit: (value: PromptCreate) => void
  submitting: boolean
}

interface FormErrors {
  title?: string
  content?: string
}

// Mirrors the backend's actual Pydantic constraints (PromptBase in
// backend/app/models.py: title min_length=1 max_length=200, content
// min_length=1) - not stricter, so nothing the client rejects would have
// been accepted by the server anyway.
function validateTitle(value: string): string | undefined {
  if (!value.trim()) return 'Title is required.'
  if (value.length > 200) return 'Title must be 200 characters or fewer.'
  return undefined
}

function validateContent(value: string): string | undefined {
  if (!value.trim()) return 'Content is required.'
  return undefined
}

/** The shared create/edit form (title, content, description, collection,
 * tags, submit/cancel) used by both PromptCreatePage and PromptEditPage -
 * one implementation so the two flows can't drift in validation or
 * layout. Owns its own field state, initialized from initialValue.
 *
 * Validation runs on submit (not on every keystroke, to avoid nagging a
 * field the user hasn't finished with yet) and then live-clears per field
 * as it's corrected. `noValidate` on the form suppresses the browser's own
 * inconsistent validation bubble in favor of this in-app FieldError, which
 * matches the rest of the app's error styling and is screen-reader
 * announced (FieldError uses role="alert"). */
export function PromptForm({ initialValue, submitLabel, onSubmit, submitting }: PromptFormProps) {
  const [title, setTitle] = useState(initialValue?.title ?? '')
  const [content, setContent] = useState(initialValue?.content ?? '')
  const [description, setDescription] = useState(initialValue?.description ?? '')
  const [collectionId, setCollectionId] = useState<string | null>(initialValue?.collection_id ?? null)
  const [tags, setTags] = useState<string[]>(initialValue?.tags ?? [])
  const [errors, setErrors] = useState<FormErrors>({})

  const { data: collections = [], error: collectionsError } = useCollections()
  const { data: allTags = [], error: tagsError } = useTags()

  function handleTitleChange(value: string) {
    setTitle(value)
    if (errors.title) setErrors((prev) => ({ ...prev, title: validateTitle(value) }))
  }

  function handleContentChange(value: string) {
    setContent(value)
    if (errors.content) setErrors((prev) => ({ ...prev, content: validateContent(value) }))
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const nextErrors: FormErrors = {
      title: validateTitle(title),
      content: validateContent(content),
    }
    setErrors(nextErrors)
    if (nextErrors.title) {
      document.getElementById('prompt-title')?.focus()
      return
    }
    if (nextErrors.content) {
      document.getElementById('prompt-content')?.focus()
      return
    }
    onSubmit({
      title,
      content,
      description: description || null,
      collection_id: collectionId,
      tags,
    })
  }

  const invalidFieldClasses =
    'border-red-400 focus:border-red-500 focus-visible:outline-red-600'
  const validFieldClasses =
    'border-slate-300 focus:border-blue-500 focus-visible:outline-blue-600'

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div>
        <label htmlFor="prompt-title" className="block text-sm font-medium text-slate-700">
          Title
        </label>
        <input
          id="prompt-title"
          type="text"
          required
          maxLength={200}
          value={title}
          onChange={(event) => handleTitleChange(event.target.value)}
          aria-invalid={Boolean(errors.title)}
          aria-describedby={errors.title ? 'prompt-title-error' : undefined}
          className={`mt-1 w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 ${
            errors.title ? invalidFieldClasses : validFieldClasses
          }`}
        />
        <FieldError id="prompt-title-error" message={errors.title} />
      </div>

      <div>
        <label htmlFor="prompt-content" className="block text-sm font-medium text-slate-700">
          Content
        </label>
        <textarea
          id="prompt-content"
          required
          rows={6}
          value={content}
          onChange={(event) => handleContentChange(event.target.value)}
          placeholder="Use {{variable}} for placeholders"
          aria-invalid={Boolean(errors.content)}
          aria-describedby={errors.content ? 'prompt-content-error' : undefined}
          className={`mt-1 w-full rounded-md border px-3 py-2 font-mono text-sm focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 ${
            errors.content ? invalidFieldClasses : validFieldClasses
          }`}
        />
        <FieldError id="prompt-content-error" message={errors.content} />
      </div>

      <div>
        <label htmlFor="prompt-description" className="block text-sm font-medium text-slate-700">
          Description <span className="font-normal text-slate-400">(optional)</span>
        </label>
        <input
          id="prompt-description"
          type="text"
          maxLength={500}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-blue-600"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700">Collection</label>
        {collectionsError ? (
          <div className="mt-1">
            <ErrorMessageFromError error={collectionsError} />
          </div>
        ) : (
          <div className="mt-1">
            <CollectionSelect collections={collections} value={collectionId} onChange={setCollectionId} />
          </div>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700">Tags</label>
        {tagsError ? (
          <div className="mt-1">
            <ErrorMessageFromError error={tagsError} />
          </div>
        ) : (
          <div className="mt-1">
            <TagInput value={tags} onChange={setTags} suggestions={allTags} />
          </div>
        )}
      </div>

      <Button type="submit" loading={submitting}>
        {submitLabel}
      </Button>
    </form>
  )
}
