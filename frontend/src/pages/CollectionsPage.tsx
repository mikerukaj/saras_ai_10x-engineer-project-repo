import { useState, type FormEvent } from 'react'

import { useCollections, useCreateCollection, useDeleteCollection } from '../api/hooks'
import { Button } from '../components/Button'
import { CollectionListItem } from '../components/collection/CollectionListItem'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { EmptyState } from '../components/EmptyState'
import { ErrorMessageFromError } from '../components/ErrorMessage'
import { LoadingIndicator } from '../components/LoadingIndicator'
import { Page } from '../components/Page'

/** List, create, and delete collections (FR-007). Deleting a collection
 * unassigns (not deletes) its prompts server-side (FR-008). */
export function CollectionsPage() {
  const { data: collections, isLoading, error } = useCollections()
  const createCollection = useCreateCollection()
  const deleteCollection = useDeleteCollection()

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null)

  function handleCreate(event: FormEvent) {
    event.preventDefault()
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
      <form onSubmit={handleCreate} className="mb-6 flex flex-col gap-2 sm:flex-row">
        <input
          type="text"
          required
          minLength={1}
          maxLength={100}
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Collection name"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <input
          type="text"
          maxLength={500}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Description (optional)"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
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
