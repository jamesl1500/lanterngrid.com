'use client'

import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import { useRef, useState } from 'react'

import { browserApi } from '@/lib/api'
import { languageLabels, type Snippet } from '@/lib/snippets'

/** The { } button by the chat box: pick one of your snippets to share. */
export function SnippetPicker({
  username,
  onPick,
}: {
  username: string
  onPick: (snippet: Snippet) => void
}) {
  const [open, setOpen] = useState(false)
  const details = useRef<HTMLDetailsElement>(null)
  const { data, isPending, isError } = useQuery({
    queryKey: ['snippets', 'mine', username],
    queryFn: async () => {
      const { data } = await browserApi.GET('/v1/users/{username}/snippets', {
        params: { path: { username }, query: { limit: 50 } },
      })
      if (!data) throw new Error('Could not load snippets.')
      return data.items
    },
    enabled: open,
  })

  return (
    <details ref={details} className="relative" onToggle={(e) => setOpen(e.currentTarget.open)}>
      <summary
        aria-label="Share a snippet"
        title="Share a snippet"
        className="flex h-10 cursor-pointer list-none items-center border-2 border-line-strong bg-sunk px-2.5 font-mono text-sm text-violet select-none hover:bg-surface [&::-webkit-details-marker]:hidden"
      >
        {'{ }'}
      </summary>
      <div className="absolute bottom-full left-0 z-30 mb-2 grid max-h-80 w-72 overflow-y-auto border-2 border-line-strong bg-surface shadow-hard">
        <p className="border-b border-line px-3 py-2 font-mono text-xs text-ink-3 uppercase">
          Your snippets
        </p>
        {isPending ? (
          <p className="px-3 py-4 text-sm text-ink-3">Loading…</p>
        ) : isError ? (
          <p className="px-3 py-4 text-sm text-coral">Couldn&apos;t load your snippets.</p>
        ) : data.length === 0 ? (
          <p className="px-3 py-4 text-sm text-ink-2">
            No snippets yet.{' '}
            <Link href="/snippets/new" className="text-violet hover:underline">
              Write one
            </Link>
          </p>
        ) : (
          data.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => {
                onPick(s)
                details.current?.removeAttribute('open')
              }}
              className="grid gap-0.5 border-b border-line px-3 py-2 text-left last:border-b-0 hover:bg-sunk"
            >
              <span className="truncate font-semibold">{s.title}</span>
              <span className="font-mono text-xs text-ink-3">
                {languageLabels[s.language]} · {s.line_count}{' '}
                {s.line_count === 1 ? 'line' : 'lines'}
                {s.visibility === 'friends' ? ' · friends only' : ''}
              </span>
            </button>
          ))
        )}
      </div>
    </details>
  )
}
