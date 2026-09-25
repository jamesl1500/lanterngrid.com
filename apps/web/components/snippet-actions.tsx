'use client'

import { Alert, Button, Select } from '@lanterngrid/ui'
import type { Route } from 'next'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import type { Visibility } from '@/lib/posts'
import type { Snippet } from '@/lib/snippets'

type Props = { snippet: Snippet; pinned: boolean }

/** Pin, share, edit and delete, for the snippet's owner. */
export function SnippetActions({ snippet, pinned: initiallyPinned }: Props) {
  const router = useRouter()
  const [pinned, setPinned] = useState(initiallyPinned)
  const [sharing, setSharing] = useState(false)
  const [caption, setCaption] = useState('')
  // A friends-only snippet can only go in a friends-only post.
  const [visibility, setVisibility] = useState<Visibility>(snippet.visibility)
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [shared, setShared] = useState<string | null>(null)

  async function run<T>(work: () => Promise<T>): Promise<T> {
    setBusy(true)
    setError(null)
    try {
      return await work()
    } finally {
      setBusy(false)
    }
  }

  async function togglePin() {
    const options = { params: { path: { type: 'snippet' as const, item_id: snippet.id } } }
    const result = await run(() =>
      attempt(() =>
        pinned
          ? browserApi.DELETE('/v1/me/pins/{type}/{item_id}', options)
          : browserApi.PUT('/v1/me/pins/{type}/{item_id}', options),
      ),
    )
    if (!result.ok) return setError(result.problem.message)
    setPinned(!pinned)
    router.refresh()
  }

  async function share() {
    const result = await run(() =>
      attempt(() =>
        browserApi.POST('/v1/posts', {
          body: { body_md: caption, visibility, images: [], snippet_id: snippet.id },
        }),
      ),
    )
    if (!result.ok) return setError(result.problem.message)
    setSharing(false)
    setCaption('')
    setShared(result.data.id)
  }

  async function remove() {
    const result = await run(() =>
      attempt(() =>
        browserApi.DELETE('/v1/snippets/{snippet_id}', {
          params: { path: { snippet_id: snippet.id } },
        }),
      ),
    )
    if (!result.ok) return setError(result.problem.message)
    router.push(`/u/${snippet.owner.username}/snippets` as Route)
    router.refresh()
  }

  return (
    <div className="grid gap-3">
      <div className="flex flex-wrap gap-2">
        <Button type="button" size="sm" variant="secondary" disabled={busy} onClick={togglePin}>
          {pinned ? 'Unpin from profile' : 'Pin to profile'}
        </Button>
        <Button
          type="button"
          size="sm"
          variant={sharing ? 'ghost' : 'secondary'}
          onClick={() => setSharing(!sharing)}
        >
          Share to feed
        </Button>
        <Button asChild size="sm" variant="secondary">
          <Link href={`/snippets/${snippet.id}/edit` as Route}>Edit</Link>
        </Button>
        {confirming ? (
          <Button type="button" size="sm" variant="ghost" disabled={busy} onClick={remove}>
            <span className="text-coral">{busy ? 'Deleting…' : 'Yes, delete it'}</span>
          </Button>
        ) : (
          <Button type="button" size="sm" variant="ghost" onClick={() => setConfirming(true)}>
            <span className="text-coral">Delete</span>
          </Button>
        )}
      </div>
      {sharing ? (
        <div className="grid gap-3 border-2 border-line-strong bg-surface p-3">
          <label htmlFor="share-caption" className="sr-only">
            Say something about it
          </label>
          <textarea
            id="share-caption"
            rows={2}
            maxLength={5000}
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            placeholder="Say something about it (optional). Markdown, #tags and @people work."
            className="w-full resize-y border border-line bg-sunk px-3 py-2 placeholder:text-ink-3 focus:border-line-strong focus:outline-none"
          />
          <div className="flex flex-wrap items-center gap-3">
            <Select
              aria-label="Who can see the post"
              value={visibility}
              disabled={snippet.visibility === 'friends'}
              onChange={(e) => setVisibility(e.target.value as Visibility)}
              className="w-40 [&_select]:h-8 [&_select]:text-sm"
            >
              <option value="public">Everyone</option>
              <option value="friends">Friends only</option>
            </Select>
            <Button type="button" size="sm" variant="accent" disabled={busy} onClick={share}>
              {busy ? 'Posting…' : 'Post it'}
            </Button>
          </div>
        </div>
      ) : null}
      {shared ? (
        <Alert tone="success">
          Shared.{' '}
          <Link href={`/p/${shared}` as Route} className="underline">
            See the post
          </Link>
        </Alert>
      ) : null}
      {error ? <Alert tone="error">{error}</Alert> : null}
    </div>
  )
}
