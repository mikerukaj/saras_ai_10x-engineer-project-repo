import { useState } from 'react'

import { Button } from '../Button'

interface CopyButtonProps {
  text: string
}

/** One-action copy-to-clipboard control for prompt content (FR-010). */
export function CopyButton({ text }: CopyButtonProps) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <Button variant="secondary" onClick={handleCopy}>
      {copied ? 'Copied!' : 'Copy content'}
    </Button>
  )
}
