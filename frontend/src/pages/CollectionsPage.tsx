import { useState, type FormEvent } from 'react'

import { useCollections, useCreateCollection, useDeleteCollection } from '../api/hooks'
import { Button } from '../components/Button'
import { CollectionListItem } from '../components/collection/CollectionListItem'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { EmptyState } from '../components/EmptyState'
import { ErrorMessageFromError } from '../components/ErrorMessage'
import { FieldError } from '../components/FieldError'
import { LoadingIndicator } from '../components/LoadingIndicator'
import { Page } from '../components/Page'

// Mirrors the backend's CollectionBase.name constraint (min_length=1,
// max_length=100 in backend/app/models.py).
function validateName(value: string): string | undefined {
  if (!value.trim()) return 'Collection name is required.'
  if (value.length > 100) return 'Collection name must be 100 characters or fewer.'
  return undefined
}

/** List, create, and delete collections (FR-007). Deleting a collection
 * unassigns (not deletes) its prompts server-side (FR-008). */
export function CollectionsPage() {
  const { data: collections, isLoading, error } = useCollections()
  const createCollection = useCreateCollection()
  const deleteCollection = useDeleteCollection()

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [nameError, setNameError] = useState<string>()
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null)

  function handleNameChange(value: string) {
    setName(value)
    if (nameError) setNameError(validateName(value))
  }

  function handleCreate(event: FormEvent) {
    event.preventDefault()
    const error = validateName(name)
    setNameError(error)
    if (error) {
      document.getElementById('collection-name')?.focus()
      return
    }
    createCollection.mutate(
      { name, description: description || null },
      {
        onSuccess: () => {
          setName('')
          setDescription('')
        },
      },
    )
  }

  return (
    <Page title="Collections">
      <form onSubmit={handleCreate} className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-start" noValidate>
        <div className="flex-1">
          <input
            id="collection-name"
            type="text"
            required
            maxLength={100}
            value={name}
            onChange={(event) => handleNameChange(event.target.value)}
            placeholder="Collection name"
            aria-invalid={Boolean(nameError)}
            aria-describedby={nameError ? 'collection-name-error' : undefined}
            className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 ${
              nameError
                ? 'border-red-400 focus:border-red-500 focus-visible:outline-red-600'
                : 'border-slate-300 focus:border-blue-500 focus-visible:outline-blue-600'
            }`}
          />
          <FieldError id="collection-name-error" message={nameError} />
        </div>
        <input
          type="text"
          maxLength={500}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Description (optional)"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-blue-600"
        />
        <Button type="submit" loading={createCollection.isPending}>
          Create
        </Button>
      </form>

      {createCollection.error && <ErrorMessageFromError error={createCollection.error} />}
      {deleteCollection.error && <ErrorMessageFromError error={deleteCollection.error} />}
      {isLoading && <LoadingIndicator label="Loading collections…" />}
      {error && <ErrorMessageFromError error={error} />}

      {collections && collections.length === 0 && <EmptyState message="No collections yet." />}

      {collections && collections.length > 0 && (
        <ul className="space-y-3">
          {collections.map((collection) => (
            <li key={collection.id}>
              <CollectionListItem
                collection={collection}
                onDelete={() => setPendingDeleteId(collection.id)}
              />
            </li>
          ))}
        </ul>
      )}

      <ConfirmDialog
        open={pendingDeleteId !== null}
        title="Delete this collection?"
        message="Prompts in this collection won't be deleted — they'll show as having no collection."
        confirmLabel="Delete"
        confirming={deleteCollection.isPending}
        onCancel={() => setPendingDeleteId(null)}
        onConfirm={() => {
          if (pendingDeleteId) {
            deleteCollection.mutate(pendingDeleteId, { onSettled: () => setPendingDeleteId(null) })
          }
        }}
      />
    </Page>
  )
}
