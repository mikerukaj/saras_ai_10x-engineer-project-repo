import { ApiError, type ApiErrorKind } from '../api/client'

interface ErrorMessageProps {
  kind: ApiErrorKind
  detail?: string
}

const copyByKind: Record<ApiErrorKind, string> = {
  invalid: 'That input isn’t valid. Please check the highlighted fields and try again.',
  'not-found': 'We couldn’t find that — it may have been deleted by someone else.',
  unreachable: 'We can’t reach the server right now. Check your connection and try again.',
  unknown: 'Something went wrong. Please try again.',
}

/** Renders one of the three non-technical error kinds the API contract
 * distinguishes by HTTP status (FR-009) — never by parsing `detail` text. */
export function ErrorMessage({ kind, detail }: ErrorMessageProps) {
  return (
    <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
      <p className="font-medium">{copyByKind[kind]}</p>
      {detail && <p className="mt-1 text-red-700/80">{detail}</p>}
    </div>
  )
}

/** Convenience wrapper so callers can pass an unknown thrown value (e.g.
 * from a TanStack Query `error`) directly. */
export function ErrorMessageFromError({ error }: { error: unknown }) {
  if (error instanceof ApiError) {
    return <ErrorMessage kind={error.kind} detail={error.message} />
  }
  return <ErrorMessage kind="unknown" />
}
