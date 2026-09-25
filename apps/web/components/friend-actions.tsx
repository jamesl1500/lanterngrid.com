'use client'

import type { Schemas } from '@lanterngrid/api-client'
import { Alert, Button } from '@lanterngrid/ui'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import { answerRequest, type RequestAction } from '@/lib/friends'

type Props = { username: string; relationship: Schemas['Relationship'] }
type Call = () => Promise<{ ok: true } | { ok: false; problem: { message: string } }>

/** The friend button on someone's profile, plus unfriend and block behind a menu. */
export function FriendActions({ username, relationship }: Props) {
  const router = useRouter()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirmBlock, setConfirmBlock] = useState(false)
  const { status, request_id: requestId } = relationship
  const path = { params: { path: { username } } }

  async function run(call: Call) {
    setBusy(true)
    setError(null)
    const result = await call()
    setBusy(false)
    setConfirmBlock(false)
    if (!result.ok) setError(result.problem.message)
    router.refresh()
  }

  const request = (action: RequestAction) => () =>
    requestId ? run(() => answerRequest(requestId, action)) : undefined
  const addFriend = () =>
    run(() => attempt(() => browserApi.POST('/v1/friend-requests', { body: { username } })))
  const unfriend = () =>
    run(() => attempt(() => browserApi.DELETE('/v1/me/friends/{username}', path)))
  const block = () => run(() => attempt(() => browserApi.PUT('/v1/me/blocks/{username}', path)))
  const unblock = () =>
    run(() => attempt(() => browserApi.DELETE('/v1/me/blocks/{username}', path)))

  if (status === 'self') return null

  return (
    <div className="grid justify-items-end gap-2">
      <div className="flex flex-wrap items-center justify-end gap-2">
        {status === 'none' ? (
          <Button size="sm" variant="accent" disabled={busy} onClick={addFriend}>
            Add friend
          </Button>
        ) : status === 'request_sent' ? (
          <>
            <span className="label">request sent</span>
            <Button size="sm" variant="secondary" disabled={busy} onClick={request('cancel')}>
              Cancel request
            </Button>
          </>
        ) : status === 'request_received' ? (
          <>
            <Button size="sm" variant="accent" disabled={busy} onClick={request('accept')}>
              Accept request
            </Button>
            <Button size="sm" variant="secondary" disabled={busy} onClick={request('decline')}>
              Decline
            </Button>
          </>
        ) : status === 'friends' ? (
          <span className="border-2 border-lime bg-lime-soft px-2 py-1 font-mono text-xs text-lime">
            ✓ friends
          </span>
        ) : (
          <Button size="sm" variant="secondary" disabled={busy} onClick={unblock}>
            Unblock
          </Button>
        )}
        {status !== 'blocked' ? (
          <details className="group relative">
            <summary
              aria-label="More actions"
              className="flex h-8 cursor-pointer list-none items-center border-2 border-line-strong bg-surface px-2 font-mono text-sm select-none hover:bg-sunk [&::-webkit-details-marker]:hidden"
            >
              •••
            </summary>
            <div className="absolute right-0 z-20 mt-1 grid w-52 border-2 border-line-strong bg-surface shadow-hard">
              {status === 'friends' ? (
                <button
                  type="button"
                  disabled={busy}
                  onClick={unfriend}
                  className="px-3 py-2 text-left font-mono text-sm hover:bg-sunk"
                >
                  Unfriend
                </button>
              ) : null}
              {confirmBlock ? (
                <button
                  type="button"
                  disabled={busy}
                  onClick={block}
                  className="bg-coral-soft px-3 py-2 text-left font-mono text-sm text-coral hover:bg-coral hover:text-ground"
                >
                  Yes, block @{username}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setConfirmBlock(true)}
                  className="px-3 py-2 text-left font-mono text-sm text-coral hover:bg-sunk"
                >
                  Block @{username}
                </button>
              )}
            </div>
          </details>
        ) : null}
      </div>
      {error ? <Alert tone="error">{error}</Alert> : null}
    </div>
  )
}
