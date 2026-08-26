import { useState } from 'react'

import { useDeleteTag, useRenameTag, useTags } from '../api/hooks'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { EmptyState } from '../components/EmptyState'
import { ErrorMessageFromError } from '../components/ErrorMessage'
import { LoadingIndicator } from '../components/LoadingIndicator'
import { Page } from '../components/Page'
import { TagListItem } from '../components/tag/TagListItem'

/** Browse every tag in use with its prompt_count, rename a tag, delete a
 * tag (FR-033, FR-034). */
export function TagsPage() {
  const { data: tags, isLoading, error } = useTags()
  const renameTag = useRenameTag()
  const deleteTag = useDeleteTag()
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null)

  return (
    <Page title="Tags">
      {isLoading && <LoadingIndicator label="Loading tags…" />}
      {error && <ErrorMessageFromError error={error} />}
      {renameTag.error && <ErrorMessageFromError error={renameTag.error} />}

      {tags && tags.length === 0 && <EmptyState message="No tags yet — tag a prompt to create one." />}

      {tags && tags.length > 0 && (
        <ul className="space-y-3">
          {tags.map((tag) => (
            <li key={tag.id}>
              <TagListItem
                tag={tag}
                onRename={(name) => renameTag.mutate({ tagId: tag.id, name })}
                onDelete={() => setPendingDeleteId(tag.id)}
              />
            </li>
          ))}
        </ul>
      )}

      <ConfirmDialog
        open={pendingDeleteId !== null}
        title="Delete this tag?"
        message="It will be removed from every prompt that carries it. Those prompts won't be deleted."
        confirmLabel="Delete"
        onCancel={() => setPendingDeleteId(null)}
        onConfirm={() => {
          if (pendingDeleteId) deleteTag.mutate(pendingDeleteId)
          setPendingDeleteId(null)
        }}
      />
    </Page>
  )
}
