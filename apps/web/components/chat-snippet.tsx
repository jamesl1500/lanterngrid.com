'use client'

import type { Route } from 'next'
import Link from 'next/link'
import { useEffect, useState } from 'react'

import { highlightPreview } from '@/app/messages/actions'
import { languageLabels, type Snippet } from '@/lib/snippets'

import { CopyButton } from './copy-button'

const PREVIEW_LINES = 10
// Highlighted previews by snippet version, so scrolling and re-renders don't ask again.
const highlighted = new Map<string, string>()

/** A snippet shared in a chat: title, the first lines of code and a link to the rest. */
export function ChatSnippet({ snippet }: { snippet: Snippet }) {
  const href = `/snippets/${snippet.id}` as Route
  const lines = snippet.content.split('\n')
  const preview = lines.slice(0, PREVIEW_LINES).join('\n')
  const hidden = Math.max(lines.length - PREVIEW_LINES, 0)
  const key = `${snippet.id}:${snippet.updated_at}`
  const [html, setHtml] = useState(() => highlighted.get(key) ?? null)

  useEffect(() => {
    if (highlighted.has(key)) return
    let current = true
    highlightPreview(preview, snippet.language)
      .then((result) => {
        highlighted.set(key, result)
        if (current) setHtml(result)
      })
      // Plain code is fine if highlighting fails.
      .catch(() => {})
    return () => {
      current = false
    }
  }, [key, preview, snippet.language])

  return (
    <div className="grid w-full min-w-0 grid-cols-1 gap-1 border-2 border-l-4 border-line-strong border-l-violet bg-surface px-3 pt-2 pb-3">
      <div className="flex items-start justify-between gap-3">
        <Link href={href} className="min-w-0 truncate font-semibold hover:underline">
          {snippet.title}
        </Link>
        <span className="shrink-0 font-mono text-xs text-violet">
          {languageLabels[snippet.language]}
        </span>
      </div>
      <figure className="code-block my-1 min-w-0 border-2 border-line-strong bg-sunk">
        <figcaption className="flex items-center justify-between gap-3 border-b border-line px-3 py-1 font-mono text-[0.68rem] tracking-[0.08em] text-ink-3">
          <span className="truncate">{snippet.filename ?? `${snippet.line_count} lines`}</span>
          <CopyButton text={snippet.content} className="uppercase hover:text-ink" />
        </figcaption>
        {html ? (
          // Shiki escapes the code; the HTML is only its own spans.
          <div dangerouslySetInnerHTML={{ __html: html }} />
        ) : (
          <pre>
            <code>{preview}</code>
          </pre>
        )}
        {hidden ? (
          <div className="border-t border-line px-3 py-1.5 font-mono text-xs">
            <Link href={href} className="text-violet hover:underline">
              {hidden} more {hidden === 1 ? 'line' : 'lines'} →
            </Link>
          </div>
        ) : null}
      </figure>
    </div>
  )
}
