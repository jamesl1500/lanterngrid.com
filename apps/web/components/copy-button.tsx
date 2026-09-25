'use client'

import { useState } from 'react'

/** Copies text to the clipboard and says so for a moment. */
export function CopyButton({ text, className }: { text: string; className?: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      type="button"
      className={className}
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text)
          setCopied(true)
          setTimeout(() => setCopied(false), 1500)
        } catch {
          // Clipboard blocked (insecure context or denied); nothing useful to say.
        }
      }}
    >
      <span aria-live="polite">{copied ? 'copied' : 'copy'}</span>
    </button>
  )
}
