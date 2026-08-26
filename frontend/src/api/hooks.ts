import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
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

/** Unwrap an openapi-fetch result, throwing a typed ApiError on failure so
 * TanStack Query's error state (surfaced via ErrorMessage) is populated.
 * The return type is asserted to T (rather than inferred structurally)
 * because openapi-typescript marks server-generated fields as optional
 * (see the WithRequired comment in client.ts) even though a successful
 * response always has them populated. */
function unwrap<T>({ data, error, response }: { data?: unknown; error?: unknown; response: Response }): T {
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
      const result = await client.GET('/prompts', {
        params: {
          query: {
            search: filters.search || undefined,
            collection_id: filters.collectionId || undefined,
            tags: filters.tags?.length ? filters.tags.join(',') : undefined,
          },
        },
      })
      return unwrap<{ prompts: Prompt[] }>(result).prompts
    },
  })
}

export function usePrompt(promptId: string | undefined) {
  return useQuery({
    queryKey: ['prompt', promptId],
    queryFn: async () => {
      const result = await client.GET('/prompts/{prompt_id}', {
        params: { path: { prompt_id: promptId as string } },
      })
      return unwrap<Prompt>(result)
    },
    enabled: promptId !== undefined,
  })
}

export function useCreatePrompt() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (body: PromptCreate) => {
      const result = await client.POST('/prompts', { body })
      return unwrap<Prompt>(result)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })
}

export function useUpdatePrompt(promptId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (body: PromptPatch) => {
      const result = await client.PATCH('/prompts/{prompt_id}', {
        params: { path: { prompt_id: promptId } },
        body,
      })
      return unwrap<Prompt>(result)
    },
    onSuccess: (updated: Prompt) => {
      queryClient.setQueryData(['prompt', promptId], updated)
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })
}

export function useDeletePrompt() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (promptId: string) => {
      const result = await client.DELETE('/prompts/{prompt_id}', {
        params: { path: { prompt_id: promptId } },
      })
      unwrap(result)
    },
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
      const result = await client.GET('/prompts/{prompt_id}/versions', {
        params: { path: { prompt_id: promptId as string } },
      })
      return unwrap<{ versions: PromptVersion[] }>(result).versions
    },
    enabled: promptId !== undefined,
  })
}

export function useCreateVersion(promptId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (label: string | undefined) => {
      const result = await client.POST('/prompts/{prompt_id}/versions', {
        params: { path: { prompt_id: promptId } },
        body: { label },
      })
      return unwrap<PromptVersion>(result)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompt', promptId, 'versions'] })
    },
  })
}

export function useRestoreVersion(promptId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (versionId: string) => {
      const result = await client.POST('/prompts/{prompt_id}/versions/{version_id}/restore', {
        params: { path: { prompt_id: promptId, version_id: versionId } },
      })
      return unwrap<Prompt>(result)
    },
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
    mutationFn: async (versionId: string) => {
      const result = await client.DELETE('/prompts/{prompt_id}/versions/{version_id}', {
        params: { path: { prompt_id: promptId, version_id: versionId } },
      })
      unwrap(result)
    },
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
      const result = await client.GET('/collections', {})
      return unwrap<{ collections: Collection[] }>(result).collections
    },
  })
}

export function useCreateCollection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (body: CollectionCreate) => {
      const result = await client.POST('/collections', { body })
      return unwrap<Collection>(result)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}

export function useDeleteCollection() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (collectionId: string) => {
      const result = await client.DELETE('/collections/{collection_id}', {
        params: { path: { collection_id: collectionId } },
      })
      unwrap(result)
    },
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
      const result = await client.GET('/tags', {})
      return unwrap<{ tags: Tag[] }>(result).tags
    },
  })
}

export function useRenameTag() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ tagId, name }: { tagId: string; name: string }) => {
      const result = await client.PATCH('/tags/{tag_id}', {
        params: { path: { tag_id: tagId } },
        body: { name },
      })
      return unwrap<Tag>(result)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })
}

export function useDeleteTag() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (tagId: string) => {
      const result = await client.DELETE('/tags/{tag_id}', {
        params: { path: { tag_id: tagId } },
      })
      unwrap(result)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
    },
  })
}

export type { Collection, Prompt, Tag }
