import { Link } from 'react-router-dom'

import { Page } from '../components/Page'

/** Generic "page not found" fallback for an unmatched route, with a link
 * back to the prompt list. */
export function NotFoundPage() {
  return (
    <Page title="Page not found">
      <p className="text-sm text-slate-600">
        We couldn’t find that page.{' '}
        <Link to="/" className="font-medium text-blue-600 hover:underline">
          Back to prompts
        </Link>
      </p>
    </Page>
  )
}
