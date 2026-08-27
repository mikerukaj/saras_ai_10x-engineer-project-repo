import { useState, type FormEvent } from 'react'

import { useCollections, useTags } from '../../api/hooks'
import type { PromptCreate } from '../../api/client'
import { Button } from '../Button'
import { ErrorMessageFromError } from '../ErrorMessage'
import { TagInput } from '../tag/TagInput'
import { CollectionSelect } from './CollectionSelect'

interface PromptFormProps {
  initialValue?: Partial<PromptCreate>
  submitLabel: string
  onSubmit: (value: PromptCreate) => void
  submitting: boolean
}

/** The shared create/edit form (title, content, description, collection,
 * tags, submit/cancel) used by both PromptCreatePage and PromptEditPage -
 * one implementation so the two flows can't drift in validation or
 * layout. Owns its own field state, initialized from initialValue. */
export function PromptForm({ initialValue, submitLabel, onSubmit, submitting }: PromptFormProps) {
  const [title, setTitle] = useState(initialValue?.title ?? '')
  const [content, setContent] = useState(initialValue?.content ?? '')
  const [description, setDescription] = useState(initialValue?.description ?? '')
  const [collectionId, setCollectionId] = useState<string | null>(initialValue?.collection_id ?? null)
  const [tags, setTags] = useState<string[]>(initialValue?.tags ?? [])

  const { data: collections = [], error: collectionsError } = useCollections()
  const { data: allTags = [], error: tagsError } = useTags()

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    onSubmit({
      title,
      content,
      description: description || null,
      collection_id: collectionId,
      tags,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="prompt-title" className="block text-sm font-medium text-slate-700">
          Title
        </label>
        <input
          id="prompt-title"
          type="text"
          required
          minLength={1}
          maxLength={200}
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-blue-600"
        />
      </div>

      <div>
        <label htmlFor="prompt-content" className="block text-sm font-medium text-slate-700">
          Content
        </label>
        <textarea
          id="prompt-content"
          required
          minLength={1}
          rows={6}
          value={content}
          onChange={(event) => setContent(event.target.value)}
          placeholder="Use {{variable}} for placeholders"
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-sm focus:border-blue-500 focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-blue-600"
        />
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
