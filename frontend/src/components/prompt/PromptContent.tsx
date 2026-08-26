const PLACEHOLDER_PATTERN = /(\{\{\s*[\w.-]+\s*\}\})/g

interface PromptContentProps {
  content: string
}

/** Renders prompt content with `{{variable}}`-style placeholders visually
 * distinguished from surrounding text (FR-004). */
export function PromptContent({ content }: PromptContentProps) {
  // A capturing group in the split pattern means the matched delimiters
  // are interspersed in the result at odd indices - no separate,
  // stateful regex .test() call needed to tell placeholders from text.
  const parts = content.split(PLACEHOLDER_PATTERN)

  return (
    <pre className="whitespace-pre-wrap break-words font-sans text-sm text-slate-800">
      {parts.map((part, index) =>
        index % 2 === 1 ? (
          <mark
            key={index}
            className="rounded bg-amber-100 px-0.5 font-mono text-amber-800"
          >
            {part}
          </mark>
        ) : (
          <span key={index}>{part}</span>
        ),
      )}
    </pre>
  )
}
