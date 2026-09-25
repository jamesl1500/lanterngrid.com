'use client'

import { Alert, Button, Select } from '@lanterngrid/ui'
import type { Route } from 'next'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import type { Visibility } from '@/lib/posts'

type Props = { repoId: string; fullName: string; pinned: boolean }

/** Pin, share and remove, for the person who added the repo. */
export function RepoActions({ repoId, fullName, pinned: initiallyPinned }: Props) {
  const router = useRouter()
  const [pinned, setPinned] = useState(initiallyPinned)
  const [sharing, setSharing] = useState(false)
  const [caption, setCaption] = useState('')
  const [visibility, setVisibility] = useState<Visibility>('public')
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
    const options = { params: { path: { type: 'repo' as const, item_id: repoId } } }
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
          body: { body_md: caption, visibility, images: [], repo_id: repoId },
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
        browserApi.DELETE('/v1/repos/{repo_id}', { params: { path: { repo_id: repoId } } }),
      ),
    )
    if (!result.ok) return setError(result.problem.message)
    router.refresh()
  }

  const captionId = `share-${repoId}`
  return (
    <div className="grid gap-3 border-t border-line pt-3">
      <div className="flex flex-wrap gap-2">
        <Button type="button" size="sm" variant="secondary" disabled={busy} onClick={togglePin}>
          {pinned ? 'Unpin' : 'Pin to profile'}
        </Button>
        <Button
          type="button"
          size="sm"
          variant={sharing ? 'ghost' : 'secondary'}
          onClick={() => setSharing(!sharing)}
        >
          Share to feed
        </Button>
        {confirming ? (
          <Button type="button" size="sm" variant="ghost" disabled={busy} onClick={remove}>
            <span className="text-coral">{busy ? 'Removing…' : 'Yes, remove it'}</span>
          </Button>
        ) : (
          <Button
            type="button"
            size="sm"
            variant="ghost"
            aria-label={`Remove ${fullName}`}
            onClick={() => setConfirming(true)}
          >
            <span className="text-coral">Remove</span>
          </Button>
        )}
      </div>
      {sharing ? (
        <div className="grid gap-3">
          <label htmlFor={captionId} className="sr-only">
            Say something about it
          </label>
          <textarea
            id={captionId}
            rows={2}
            maxLength={5000}
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            placeholder="What is it, and why should people look? Markdown, #tags and @people work."
            className="w-full resize-y border border-line bg-sunk px-3 py-2 text-sm placeholder:text-ink-3 focus:border-line-strong focus:outline-none"
          />
          <div className="flex flex-wrap items-center gap-3">
            <Select
              aria-label="Who can see the post"
              value={visibility}
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
