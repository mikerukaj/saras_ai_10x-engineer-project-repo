import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { useDeletePrompt, usePrompt } from '../api/hooks'
import { Card } from '../components/Card'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { ErrorMessageFromError } from '../components/ErrorMessage'
import { LoadingIndicator } from '../components/LoadingIndicator'
import { Page } from '../components/Page'
import { CopyButton } from '../components/prompt/CopyButton'
import { PromptContent } from '../components/prompt/PromptContent'
import { VersionHistoryPanel } from '../components/prompt/VersionHistoryPanel'
import { TagBadge } from '../components/tag/TagBadge'

/** View a prompt's full details (content with placeholders highlighted),
 * copy its content, delete it (with confirmation), and browse/restore/
 * checkpoint/delete its version history inline (FR-004, FR-006, FR-010,
 * FR-027-030). */
export function PromptDetailPage() {
  const { promptId } = useParams<{ promptId: string }>()
  const navigate = useNavigate()
  const { data: prompt, isLoading, error } = usePrompt(promptId)
  const deletePrompt = useDeletePrompt()
  const [confirmingDelete, setConfirmingDelete] = useState(false)

  if (isLoading) return <LoadingIndicator label="Loading prompt…" />
  if (error) return <ErrorMessageFromError error={error} />
  if (!prompt) return null

  return (
    <Page
      title={prompt.title}
      actions={
        <>
          <Link
            to={`/prompts/${prompt.id}/edit`}
            className="inline-flex items-center justify-center rounded-md bg-white px-3 py-2 text-sm font-medium text-slate-900 ring-1 ring-inset ring-slate-300 hover:bg-slate-50"
          >
            Edit
          </Link>
          <CopyButton text={prompt.content} />
          <button
            type="button"
            onClick={() => setConfirmingDelete(true)}
            className="inline-flex items-center justify-center rounded-md bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            Delete
          </button>
        </>
      }
    >
      {deletePrompt.error && <ErrorMessageFromError error={deletePrompt.error} />}

      <Card>
        {prompt.description && <p className="mb-3 text-sm text-slate-600">{prompt.description}</p>}
        <div className="mb-3 flex flex-wrap items-center gap-1.5">
          <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
            {prompt.collection_id ? 'In a collection' : 'No collection'}
          </span>
          {prompt.tags.map((tag) => (
            <TagBadge key={tag.id} tag={tag} />
          ))}
        </div>
        <PromptContent content={prompt.content} />
      </Card>

      <section className="mt-6">
        <h2 className="mb-2 text-sm font-semibold text-slate-900">Version history</h2>
        <VersionHistoryPanel promptId={prompt.id} />
      </section>

      <ConfirmDialog
        open={confirmingDelete}
        title="Delete this prompt?"
        message="This can't be undone. Its version history will be deleted along with it."
        confirmLabel="Delete"
        confirming={deletePrompt.isPending}
        onCancel={() => setConfirmingDelete(false)}
        onConfirm={() => {
          deletePrompt.mutate(prompt.id, {
            onSuccess: () => navigate('/'),
            onSettled: () => setConfirmingDelete(false),
          })
        }}
      />
    </Page>
  )
}
