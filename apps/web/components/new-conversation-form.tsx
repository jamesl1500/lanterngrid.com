'use client'

import { Alert, Button, Field, Input } from '@lanterngrid/ui'
import type { Route } from 'next'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import { MAX_GROUP_SIZE, MAX_GROUP_TITLE } from '@/lib/messages'
import type { Person } from '@/lib/people'

import { FriendPicker } from './friend-picker'

/** Pick one friend for a direct message, or several (and a name) for a group. */
export function NewConversationForm({ friends }: { friends: Person[] }) {
  const router = useRouter()
  const [selected, setSelected] = useState<string[]>([])
  const [title, setTitle] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const group = selected.length > 1

  async function start(event: React.FormEvent) {
    event.preventDefault()
    if (selected.length === 0) return
    setBusy(true)
    setError(null)
    const result = await attempt(() =>
      browserApi.POST('/v1/conversations', {
        body: { usernames: selected, title: group ? title.trim() || null : null },
      }),
    )
    if (result.ok) return router.push(`/messages/${result.data.id}` as Route)
    setBusy(false)
    setError(result.problem.message)
  }

  return (
    <form onSubmit={start} className="grid gap-4">
      <FriendPicker
        friends={friends}
        selected={selected}
        onChange={setSelected}
        max={MAX_GROUP_SIZE - 1}
      />
      {group ? (
        <Field id="group-title" label="Group name" hint="Optional. Everyone in the group sees it.">
          <Input
            id="group-title"
            value={title}
            maxLength={MAX_GROUP_TITLE}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Release crew"
          />
        </Field>
      ) : null}
      {error ? <Alert tone="error">{error}</Alert> : null}
      <div className="flex items-center justify-between gap-4">
        <span className="font-mono text-xs text-ink-3">
          {selected.length === 0
            ? 'pick one friend, or a few for a group'
            : group
              ? `group of ${selected.length + 1}`
              : 'direct message'}
        </span>
        <Button
          type="submit"
          disabled={busy || selected.length === 0}
          className="bg-magenta text-[#0c1017]"
        >
          {group ? 'Start group' : 'Message'}
        </Button>
      </div>
    </form>
  )
}
