import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  ApiError,
  client,
  toApiError,
  type Collection,
  type CollectionCreate,
  type Prompt,
  type PromptCreate,
  type PromptPatch,
  type PromptVersion,
  type Tag,
} from './client'

type FetchResult = { data?: unknown; error?: unknown; response: Response }

/** Await an openapi-fetch call and throw a typed ApiError on any failure,
 * so TanStack Query's error state (surfaced via ErrorMessage) is always
 * populated — including when the request never reaches the server at all
 * (offline, DNS failure, CORS): openapi-fetch lets that case reject the
 * promise rather than resolving with an `error` field, so it needs its own
 * catch to land on the 'unreachable' kind instead of falling through to a
 * raw, unclassified Error. The return type is asserted to T (rather than
 * inferred structurally) because openapi-typescript marks server-generated
 * fields as optional (see the WithRequired comment in client.ts) even
 * though a successful response always has them populated. */
async function request<T>(promise: Promise<FetchResult>): Promise<T> {
  let result: FetchResult
  try {
    result = await promise
  } catch {
    throw new ApiError('unreachable', 'Could not reach the server.')
  }
  const { data, error, response } = result
  if (error !== undefined || !response.ok) {
    throw toApiError(response.status, error)
  }
  return data as T
}

export interface PromptFilters {
  search?: string
  collectionId?: string
  tags?: string[]
}

// ============== Prompts ==============

export function usePrompts(filters: PromptFilters = {}) {
  return useQuery({
    queryKey: ['prompts', filters],
    queryFn: async () => {
      const { prompts } = await request<{ prompts: Prompt[] }>(
        client.GET('/prompts', {
          params: {
            query: {
              search: filters.search || undefined,
              collection_id: filters.collectionId || undefined,
              tags: filters.tags?.length ? filters.tags.join(',') : undefined,
            },
          },
        }),
      )
      return prompts
    },
  })
}

export function usePrompt(promptId: string | undefined) {
  return useQuery({
    queryKey: ['prompt', promptId],
    queryFn: async () =>
      request<Prompt>(
        client.GET('/prompts/{prompt_id}', {
          params: { path: { prompt_id: promptId as string } },
        }),
      ),
    enabled: promptId !== undefined,
  })
}

export function useCreatePrompt() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (body: PromptCreate) => request<Prompt>(client.POST('/prompts', { body })),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })
}

export function useUpdatePrompt(promptId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (body: PromptPatch) =>
      request<Prompt>(
        client.PATCH('/prompts/{prompt_id}', {
          params: { path: { prompt_id: promptId } },
          body,
        }),
      ),
    onSuccess: (updated: Prompt) => {
      queryClient.setQueryData(['prompt', promptId], updated)
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })
}

export function useDeletePrompt() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (promptId: string) =>
      request(
        client.DELETE('/prompts/{prompt_id}', {
          params: { path: { prompt_id: promptId } },
        }),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })
}

// ============== Prompt Versions ==============

export function usePromptVersions(promptId: string | undefined) {
  return useQuery({
    queryKey: ['prompt', promptId, 'versions'],
    queryFn: async () => {
      const { versions } = await request<{ versions: PromptVersion[] }>(
        client.GET('/prompts/{prompt_id}/versions', {
          params: { path: { prompt_id: promptId as string } },
        }),
      )
      return versions
    },
    enabled: promptId !== undefined,
  })
}

export function useCreateVersion(promptId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (label: string | undefined) =>
      request<PromptVersion>(
        client.POST('/prompts/{prompt_id}/versions', {
          params: { path: { prompt_id: promptId } },
          body: { label },
        }),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompt', promptId, 'versions'] })
    },
  })
}

export function useRestoreVersion(promptId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (versionId: string) =>
      request<Prompt>(
        client.POST('/prompts/{prompt_id}/versions/{version_id}/restore', {
          params: { path: { prompt_id: promptId, version_id: versionId } },
        }),
      ),
    onSuccess: (updated: Prompt) => {
      queryClient.setQueryData(['prompt', promptId], updated)
      queryClient.invalidateQueries({ queryKey: ['prompt', promptId, 'versions'] })
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })
}

export function useDeleteVersion(promptId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (versionId: string) =>
      request(
        client.DELETE('/prompts/{prompt_id}/versions/{version_id}', {
          params: { path: { prompt_id: promptId, version_id: versionId } },
        }),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompt', promptId, 'versions'] })
    },
  })
}

// ============== Collections ==============

export function useCollections() {
  return useQuery({
    queryKey: ['collections'],
    queryFn: async () => {
      const { collections } = await request<{ collections: Collection[] }>(client.GET('/collections', {}))
      return collections
    },
  })
}

export function useCreateCollection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (body: CollectionCreate) => request<Collection>(client.POST('/collections', { body })),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}

export function useDeleteCollection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (collectionId: string) =>
      request(
        client.DELETE('/collections/{collection_id}', {
          params: { path: { collection_id: collectionId } },
        }),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
      // A collection delete unassigns (not deletes) its prompts server-side
      // (FR-008) - refresh prompt data so "No collection" shows immediately.
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })
}

// ============== Tags ==============

export function useTags() {
  return useQuery({
    queryKey: ['tags'],
    queryFn: async () => {
      const { tags } = await request<{ tags: Tag[] }>(client.GET('/tags', {}))
      return tags
    },
  })
}

export function useRenameTag() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ tagId, name }: { tagId: string; name: string }) =>
      request<Tag>(
        client.PATCH('/tags/{tag_id}', {
          params: { path: { tag_id: tagId } },
          body: { name },
        }),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })
}

export function useDeleteTag() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (tagId: string) =>
      request(
        client.DELETE('/tags/{tag_id}', {
          params: { path: { tag_id: tagId } },
        }),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })
}

export type { Collection, Prompt, Tag }
