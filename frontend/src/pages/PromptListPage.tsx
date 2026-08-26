import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { useCollections, usePrompts, useTags } from '../api/hooks'
import { EmptyState } from '../components/EmptyState'
import { ErrorMessageFromError } from '../components/ErrorMessage'
import { LoadingIndicator } from '../components/LoadingIndicator'
import { Page } from '../components/Page'
import { PromptFilters, type PromptFilterState } from '../components/prompt/PromptFilters'
import { PromptListItem } from '../components/prompt/PromptListItem'

/** Browse all prompts: title, description, collection, tags. Search by
 * keyword, filter by collection and/or tags. Entry point to create/view a
 * prompt (FR-001, FR-002, FR-032). Filter state lives in the URL so
 * filtered views are bookmarkable/shareable and survive navigation. */
export function PromptListPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const filterState: PromptFilterState = {
    search: searchParams.get('search') ?? '',
    collectionId: searchParams.get('collection_id') ?? undefined,
    tagNames: searchParams.get('tags')?.split(',').filter(Boolean) ?? [],
  }

  function handleFilterChange(next: PromptFilterState) {
    const params = new URLSearchParams()
    if (next.search) params.set('search', next.search)
    if (next.collectionId) params.set('collection_id', next.collectionId)
    if (next.tagNames.length > 0) params.set('tags', next.tagNames.join(','))
    setSearchParams(params)
  }

  const { data: collections = [] } = useCollections()
  const { data: allTags = [] } = useTags()
  const {
    data: prompts,
    isLoading,
    error,
  } = usePrompts({
    search: filterState.search,
    collectionId: filterState.collectionId,
    tags: filterState.tagNames,
  })

  const collectionNameById = new Map(collections.map((c) => [c.id, c.name]))
  const hasActiveFilter = Boolean(filterState.search || filterState.collectionId || filterState.tagNames.length)

  return (
    <Page
      title="Prompts"
      actions={
        <Link
          to="/prompts/new"
          className="inline-flex items-center justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          New prompt
        </Link>
      }
    >
      <PromptFilters
        collections={collections}
        tags={allTags}
        value={filterState}
        onChange={handleFilterChange}
      />

      {isLoading && <LoadingIndicator label="Loading prompts…" />}
      {error && <ErrorMessageFromError error={error} />}

      {prompts && prompts.length === 0 && (
        <EmptyState
          message={hasActiveFilter ? 'No prompts match your filters.' : 'No prompts yet.'}
          action={
            hasActiveFilter
              ? undefined
              : { label: 'Create your first prompt', onClick: () => navigate('/prompts/new') }
          }
        />
      )}

      {prompts && prompts.length > 0 && (
        <ul className="space-y-3">
          {prompts.map((prompt) => (
            <li key={prompt.id}>
              <PromptListItem
                prompt={prompt}
                collectionName={prompt.collection_id ? collectionNameById.get(prompt.collection_id) : undefined}
              />
            </li>
          ))}
        </ul>
      )}
    </Page>
  )
}
