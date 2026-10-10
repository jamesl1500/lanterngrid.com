'use client'

import { Alert, Button, Input } from '@lanterngrid/ui'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import { MAX_CASE_NOTE, type ModerationCase } from '@/lib/moderation'

type Action = 'dismiss' | 'remove' | 'suspend'

/** A moderator's decision on an open case, with an optional note for other moderators. */
export function CaseActions({ found }: { found: ModerationCase }) {
  const router = useRouter()
  const [note, setNote] = useState('')
  const [confirmSuspend, setConfirmSuspend] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const author = found.subject_author
  const canRemove = found.subject_kind !== 'user' && !found.subject_gone
  const canSuspend = author !== null && !found.author_suspended
  const noteId = `note-${found.id}`

  async function decide(action: Action) {
    setBusy(true)
    setError(null)
    const result = await attempt(() =>
      browserApi.POST('/v1/moderation/cases/{case_id}/resolve', {
        params: { path: { case_id: found.id } },
        body: { action, note: note.trim() || null },
      }),
    )
    setBusy(false)
    setConfirmSuspend(false)
    if (!result.ok) return setError(result.problem.message)
    router.refresh()
  }

  return (
    <div className="grid gap-3 border-t border-line pt-3">
      <label htmlFor={noteId} className="sr-only">
        Note for other moderators
      </label>
      <Input
        id={noteId}
        value={note}
        maxLength={MAX_CASE_NOTE}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Note for other moderators (optional)"
      />
      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="secondary" disabled={busy} onClick={() => decide('dismiss')}>
          Dismiss
        </Button>
        {canRemove ? (
          <Button
            size="sm"
            disabled={busy}
            onClick={() => decide('remove')}
            className="bg-coral text-[#0c1017]"
          >
            Remove {found.subject_kind}
          </Button>
        ) : null}
        {canSuspend ? (
          confirmSuspend ? (
            <>
              <Button
                size="sm"
                disabled={busy}
                onClick={() => decide('suspend')}
                className="bg-coral text-[#0c1017]"
              >
                Yes, suspend @{author.username}
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setConfirmSuspend(false)}>
                Keep
              </Button>
            </>
          ) : (
            <Button size="sm" variant="ghost" onClick={() => setConfirmSuspend(true)}>
              <span className="text-coral">Suspend @{author.username}</span>
            </Button>
          )
        ) : null}
      </div>
      {confirmSuspend ? (
        <p className="text-sm text-ink-2">
          They&apos;ll be signed out and can&apos;t sign back in, everything they wrote is hidden,
          and their other open reports close too. You can lift it later.
        </p>
      ) : null}
      {error ? <Alert tone="error">{error}</Alert> : null}
    </div>
  )
}

/** Let a suspended person back in. */
export function LiftSuspensionButton({ userId, username }: { userId: string; username: string }) {
  const router = useRouter()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function lift() {
    setBusy(true)
    setError(null)
    const result = await attempt(() =>
      browserApi.DELETE('/v1/moderation/suspensions/{user_id}', {
        params: { path: { user_id: userId } },
      }),
    )
    setBusy(false)
    if (!result.ok) return setError(result.problem.message)
    router.refresh()
  }

  return (
    <div className="grid justify-items-start gap-2">
      <Button size="sm" variant="secondary" disabled={busy} onClick={lift}>
        Lift @{username}&apos;s suspension
      </Button>
      {error ? <Alert tone="error">{error}</Alert> : null}
    </div>
  )
}
