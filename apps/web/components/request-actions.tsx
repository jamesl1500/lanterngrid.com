'use client'

import { Button } from '@lanterngrid/ui'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { answerRequest, type RequestAction as Action } from '@/lib/friends'

const labels: Record<Action, string> = {
  accept: 'Accept',
  decline: 'Decline',
  cancel: 'Cancel request',
}

/** Buttons on a row in the requests lists. */
export function RequestActions({ requestId, actions }: { requestId: string; actions: Action[] }) {
  const router = useRouter()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run(action: Action) {
    setBusy(true)
    setError(null)
    const result = await answerRequest(requestId, action)
    setBusy(false)
    if (!result.ok) setError(result.problem.message)
    router.refresh()
  }

  return (
    <>
      {actions.map((action) => (
        <Button
          key={action}
          size="sm"
          variant={action === 'accept' ? 'accent' : 'secondary'}
          disabled={busy}
          onClick={() => void run(action)}
        >
          {labels[action]}
        </Button>
      ))}
      {error ? (
        <span role="alert" className="basis-full text-sm text-coral">
          {error}
        </span>
      ) : null}
    </>
  )
}
