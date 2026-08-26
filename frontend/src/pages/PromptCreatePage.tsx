import { useNavigate } from 'react-router-dom'

import { useCreatePrompt } from '../api/hooks'
import { ErrorMessageFromError } from '../components/ErrorMessage'
import { Page } from '../components/Page'
import { PromptForm } from '../components/prompt/PromptForm'

/** Create a prompt: title, content, optional description, optional
 * collection, optional tags (FR-003, FR-031). */
export function PromptCreatePage() {
  const navigate = useNavigate()
  const createPrompt = useCreatePrompt()

  return (
    <Page title="New prompt">
      {createPrompt.error && <ErrorMessageFromError error={createPrompt.error} />}
      <PromptForm
        submitLabel="Create prompt"
        submitting={createPrompt.isPending}
        onSubmit={(value) =>
          createPrompt.mutate(value, {
            onSuccess: (created) => navigate(`/prompts/${created.id}`),
          })
        }
      />
    </Page>
  )
}
