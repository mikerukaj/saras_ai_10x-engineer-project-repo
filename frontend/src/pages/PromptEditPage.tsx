import { useNavigate, useParams } from 'react-router-dom'

import { usePrompt, useUpdatePrompt } from '../api/hooks'
import { ErrorMessageFromError } from '../components/ErrorMessage'
import { LoadingIndicator } from '../components/LoadingIndicator'
import { Page } from '../components/Page'
import { PromptForm } from '../components/prompt/PromptForm'

/** Edit an existing prompt's title, content, description, collection,
 * and tags (FR-005, FR-031), saving via PATCH. */
export function PromptEditPage() {
  const { promptId } = useParams<{ promptId: string }>()
  const navigate = useNavigate()
  const { data: prompt, isLoading, error } = usePrompt(promptId)
  const updatePrompt = useUpdatePrompt(promptId as string)

  if (isLoading) return <LoadingIndicator label="Loading prompt…" />
  if (error) return <ErrorMessageFromError error={error} />
  if (!prompt) return null

  return (
    <Page title={`Edit “${prompt.title}”`}>
      {updatePrompt.error && <ErrorMessageFromError error={updatePrompt.error} />}
      <PromptForm
        initialValue={{
          title: prompt.title,
          content: prompt.content,
          description: prompt.description,
          collection_id: prompt.collection_id,
          tags: prompt.tags.map((tag) => tag.name),
        }}
        submitLabel="Save changes"
        submitting={updatePrompt.isPending}
        onSubmit={(value) =>
          updatePrompt.mutate(value, {
            onSuccess: () => navigate(`/prompts/${prompt.id}`),
          })
        }
      />
    </Page>
  )
}
