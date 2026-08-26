import createClient from 'openapi-fetch'

import type { components, paths } from './schema'

// openapi-typescript marks server-generated fields (id, created_at, ...)
// as optional, because Pydantic's default_factory makes them non-required
// on the *request* side of the schema it reads from — but every actual
// API *response* always has them populated. WithRequired re-narrows just
// those fields so components don't need `?? fallback` at every call site.
type WithRequired<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>

export type Tag = WithRequired<components['schemas']['Tag'], 'id' | 'created_at'>
export type Prompt = Omit<
  WithRequired<components['schemas']['Prompt'], 'id' | 'created_at' | 'updated_at' | 'tags'>,
  'tags'
> & { tags: Tag[] }
export type PromptCreate = components['schemas']['PromptCreate']
export type PromptUpdate = components['schemas']['PromptUpdate']
export type PromptPatch = components['schemas']['PromptPatch']
export type Collection = WithRequired<components['schemas']['Collection'], 'id' | 'created_at'>
export type CollectionCreate = components['schemas']['CollectionCreate']
export type PromptVersion = WithRequired<components['schemas']['PromptVersion'], 'id' | 'created_at'>

// Backend base URL. Overridable via VITE_API_BASE_URL for non-local
// deployments (e.g. docker-compose); defaults to the backend's documented
// local dev address (README.md Quick Start).
const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

// Typed fetch client generated from the backend's OpenAPI schema
// (src/api/schema.ts, regenerated via `npm run generate:types`) — every
// request/response shape below is checked against contracts/api-contract.md
// at build time, per research.md Decision 5.
export const client = createClient<paths>({ baseUrl })

export type ApiErrorKind = 'invalid' | 'not-found' | 'unreachable' | 'unknown'

/** A typed error carrying enough information for ErrorMessage (FR-009) to
 * distinguish invalid input / not found / backend unreachable. */
export class ApiError extends Error {
  kind: ApiErrorKind
  status?: number

  constructor(kind: ApiErrorKind, message: string, status?: number) {
    super(message)
    this.kind = kind
    this.status = status
  }
}

/** Best-effort human-readable message from a FastAPI error body. Used only
 * for display text — the *kind* of error (invalid/not-found/unreachable)
 * always comes from the HTTP status code, per api-contract.md, never from
 * this text. */
export function extractDetail(errorBody: unknown): string | undefined {
  if (errorBody && typeof errorBody === 'object' && 'detail' in errorBody) {
    const detail = (errorBody as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail
        .map((d) => (d && typeof d === 'object' && 'msg' in d ? String((d as { msg: unknown }).msg) : String(d)))
        .join('; ')
    }
  }
  return undefined
}

/** Map an openapi-fetch error result to an ApiError, per the status-code
 * rules in contracts/api-contract.md's "Error shape" section — never by
 * parsing the `detail` text. */
export function toApiError(status: number | undefined, errorBody?: unknown): ApiError {
  const detail = extractDetail(errorBody)
  if (status === undefined) {
    return new ApiError('unreachable', 'Could not reach the server.', status)
  }
  if (status === 404) {
    return new ApiError('not-found', detail ?? 'Not found.', status)
  }
  if (status === 400 || status === 422) {
    return new ApiError('invalid', detail ?? 'Invalid request.', status)
  }
  return new ApiError('unknown', detail ?? 'Something went wrong.', status)
}
