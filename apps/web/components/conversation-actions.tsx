'use client'

import { Alert, Button } from '@lanterngrid/ui'
import { useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import { MAX_GROUP_SIZE } from '@/lib/messages'
import type { Person } from '@/lib/people'

import { INBOX_KEY } from './conversation-list'
import { FriendPicker } from './friend-picker'

type Props = {
  conversationId: string
  memberCount: number
  /** Friends who aren't in the group yet, when you own it and can add people. */
  addable: Person[] | null
}

/** A group's menu: add people (for its owner) and leave. */
export function ConversationActions({ conversationId, memberCount, addable }: Props) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [adding, setAdding] = useState(false)
  const [confirmLeave, setConfirmLeave] = useState(false)
  const [selected, setSelected] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const path = { params: { path: { conversation_id: conversationId } } }
  const room = MAX_GROUP_SIZE - memberCount

  async function add() {
    setBusy(true)
    setError(null)
    const result = await attempt(() =>
      browserApi.POST('/v1/conversations/{conversation_id}/members', {
        ...path,
        body: { usernames: selected },
      }),
    )
    setBusy(false)
    if (!result.ok) return setError(result.problem.message)
    setAdding(false)
    setSelected([])
    router.refresh()
  }

  async function leave() {
    setBusy(true)
    setError(null)
    const result = await attempt(() =>
      browserApi.DELETE('/v1/conversations/{conversation_id}/members/me', path),
    )
    if (!result.ok) {
      setBusy(false)
      return setError(result.problem.message)
    }
    await queryClient.invalidateQueries({ queryKey: INBOX_KEY })
    router.push('/messages')
  }

  return (
    <>
      <details className="group relative">
        <summary
          aria-label="Group actions"
          className="flex h-8 cursor-pointer list-none items-center border-2 border-line-strong bg-surface px-2 font-mono text-sm select-none hover:bg-sunk [&::-webkit-details-marker]:hidden"
        >
          •••
        </summary>
        <div className="absolute right-0 z-20 mt-1 grid w-52 border-2 border-line-strong bg-surface shadow-hard">
          {addable ? (
            <button
              type="button"
              onClick={(e) => {
                e.currentTarget.closest('details')?.removeAttribute('open')
                setAdding(true)
              }}
              className="px-3 py-2 text-left font-mono text-sm hover:bg-sunk"
            >
              Add people
            </button>
          ) : null}
          {confirmLeave ? (
            <button
              type="button"
              disabled={busy}
              onClick={leave}
              className="bg-coral-soft px-3 py-2 text-left font-mono text-sm text-coral hover:bg-coral hover:text-ground"
            >
              Yes, leave the group
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setConfirmLeave(true)}
              className="px-3 py-2 text-left font-mono text-sm text-coral hover:bg-sunk"
            >
              Leave group
            </button>
          )}
        </div>
      </details>
      {adding && addable ? (
        <div className="absolute inset-x-0 top-full z-30 grid gap-3 border-b-2 border-line-strong bg-surface p-4 shadow-hard">
          <div className="flex items-center justify-between gap-4">
            <h2 className="font-display text-lg font-semibold">Add people</h2>
            <span className="font-mono text-xs text-ink-3">
              {room > 0 ? `room for ${room} more` : 'the group is full'}
            </span>
          </div>
          {addable.length === 0 ? (
            <p className="text-ink-2">All your friends are already here.</p>
          ) : (
            <FriendPicker
              friends={addable}
              selected={selected}
              onChange={setSelected}
              max={Math.max(room, 0)}
            />
          )}
          <div className="flex justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={() => setAdding(false)}>
              Cancel
            </Button>
            <Button
              size="sm"
              disabled={busy || selected.length === 0}
              onClick={add}
              className="bg-magenta text-[#0c1017]"
            >
              Add {selected.length || ''}
            </Button>
          </div>
        </div>
      ) : null}
      {error ? (
        <Alert tone="error" className="absolute inset-x-0 top-full z-30">
          {error}
        </Alert>
      ) : null}
    </>
  )
}
