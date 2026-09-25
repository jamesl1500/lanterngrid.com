'use client'

import { cn } from '@lanterngrid/ui'
import type { Route } from 'next'
import Link from 'next/link'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import {
  reactionInfo,
  reactions,
  toggleReaction,
  type ReactionCount,
  type ReactionKind,
} from '@/lib/posts'

type Props = { postId: string; initial: ReactionCount[]; signedIn: boolean }

const chip =
  'flex h-7 items-center gap-1.5 border px-2 font-mono text-xs transition-colors disabled:opacity-60'

/** Reaction counts, which the signed-in viewer can toggle. */
export function ReactionBar({ postId, initial, signedIn }: Props) {
  const [counts, setCounts] = useState(initial)
  const [pending, setPending] = useState(false)

  async function toggle(kind: ReactionKind) {
    const on = !counts.find((r) => r.kind === kind)?.mine
    const before = counts
    setCounts(toggleReaction(counts, kind)) // show it straight away
    setPending(true)
    const options = { params: { path: { post_id: postId, kind } } }
    const result = await attempt(() =>
      on
        ? browserApi.PUT('/v1/posts/{post_id}/reactions/{kind}', options)
        : browserApi.DELETE('/v1/posts/{post_id}/reactions/{kind}', options),
    )
    setPending(false)
    setCounts(result.ok ? result.data.reactions : before)
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {counts.map((r) => {
        const { emoji, label } = reactionInfo[r.kind]
        const text = `${label}: ${r.count}`
        return signedIn ? (
          <button
            key={r.kind}
            type="button"
            aria-pressed={r.mine}
            aria-label={text}
            title={label}
            disabled={pending}
            onClick={() => void toggle(r.kind)}
            className={cn(
              chip,
              r.mine
                ? 'border-cyan bg-cyan-soft text-ink'
                : 'border-line text-ink-2 hover:border-line-strong',
            )}
          >
            <span aria-hidden>{emoji}</span>
            {r.count}
          </button>
        ) : (
          <span key={r.kind} className={cn(chip, 'border-line text-ink-2')} title={text}>
            <span aria-hidden>{emoji}</span>
            <span className="sr-only">{label}</span>
            {r.count}
          </span>
        )
      })}
      {signedIn ? (
        <details className="group relative">
          <summary
            aria-label="Add a reaction"
            className={cn(
              chip,
              'cursor-pointer list-none border-line text-ink-3 hover:border-line-strong hover:text-ink [&::-webkit-details-marker]:hidden',
            )}
          >
            <span aria-hidden>+</span>
            <span aria-hidden>☺</span>
          </summary>
          <div className="absolute bottom-full left-0 z-20 mb-1 flex border-2 border-line-strong bg-surface shadow-hard">
            {reactions.map((r) => (
              <button
                key={r.kind}
                type="button"
                title={r.label}
                aria-label={r.label}
                disabled={pending}
                onClick={(e) => {
                  e.currentTarget.closest('details')?.removeAttribute('open')
                  void toggle(r.kind)
                }}
                className="grid size-9 place-items-center text-lg hover:bg-sunk"
              >
                {r.emoji}
              </button>
            ))}
          </div>
        </details>
      ) : counts.length === 0 ? null : (
        <Link
          href={'/signin' as Route}
          className="px-1 font-mono text-xs text-ink-3 hover:text-ink"
        >
          sign in to react
        </Link>
      )}
    </div>
  )
}
