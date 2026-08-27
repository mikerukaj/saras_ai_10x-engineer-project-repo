import { useState } from 'react'

import { Button } from '../Button'

interface CopyButtonProps {
  text: string
}

/** One-action copy-to-clipboard control for prompt content (FR-010). */
export function CopyButton({ text }: CopyButtonProps) {
  const [copied, setCopied] = useState(false)
  const [failed, setFailed] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(text)
      setFailed(false)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // Clipboard access can be denied (permissions, insecure context) -
      // that failure must surface rather than vanish as a silent no-op.
      setCopied(false)
      setFailed(true)
      setTimeout(() => setFailed(false), 3000)
    }
  }

  return (
    <div className="inline-flex flex-col items-start gap-1">
      <Button variant="secondary" onClick={handleCopy}>
        {copied ? 'Copied!' : 'Copy content'}
      </Button>
      {failed && <span className="text-xs text-red-700">Couldn’t copy — try selecting and copying manually.</span>}
    </div>
  )
}
