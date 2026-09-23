'use client'

import { Alert, Button } from '@lanterngrid/ui'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'

type Status = { tone: 'success' | 'error'; text: string } | null

function useAction() {
  const [status, setStatus] = useState<Status>(null)
  const [busy, setBusy] = useState(false)
  async function run(call: Parameters<typeof attempt>[0], success: string) {
    setBusy(true)
    setStatus(null)
    const result = await attempt(call)
    setBusy(false)
    setStatus(
      result.ok
        ? { tone: 'success', text: success }
        : { tone: 'error', text: result.problem.message },
    )
    return result.ok
  }
  return { status, busy, run }
}

export function ResendVerificationButton({ compact = false }: { compact?: boolean }) {
  const { status, busy, run } = useAction()
  if (status?.tone === 'success')
    return <span className="font-mono text-xs">Sent. Check your inbox.</span>
  return (
    <span className="inline-flex flex-wrap items-center gap-2">
      <Button
        size="sm"
        variant={compact ? 'ghost' : 'secondary'}
        disabled={busy}
        onClick={() => run(() => browserApi.POST('/v1/auth/verify-email/resend'), 'Sent')}
      >
        {busy ? 'Sending…' : 'Resend the email'}
      </Button>
      {status?.tone === 'error' ? <span className="text-sm text-coral">{status.text}</span> : null}
    </span>
  )
}

export function SendPasswordResetButton({ email }: { email: string }) {
  const { status, busy, run } = useAction()
  return (
    <div className="grid gap-3">
      {status ? <Alert tone={status.tone}>{status.text}</Alert> : null}
      <Button
        variant="secondary"
        size="sm"
        className="justify-self-start"
        disabled={busy || status?.tone === 'success'}
        onClick={() =>
          run(
            () => browserApi.POST('/v1/auth/password-reset', { body: { email } }),
            `We sent a link to ${email} to choose a new password.`,
          )
        }
      >
        {busy ? 'Sending…' : 'Email me a password link'}
      </Button>
    </div>
  )
}

export function SignOutEverywhereButton() {
  const router = useRouter()
  const { status, busy, run } = useAction()
  return (
    <div className="grid gap-3">
      {status?.tone === 'error' ? <Alert tone="error">{status.text}</Alert> : null}
      <Button
        variant="secondary"
        size="sm"
        className="justify-self-start border-coral text-coral"
        disabled={busy}
        onClick={async () => {
          if (await run(() => browserApi.POST('/v1/auth/signout-everywhere'), 'Signed out')) {
            router.push('/signin')
            router.refresh()
          }
        }}
      >
        {busy ? 'Signing out…' : 'Sign out on every device'}
      </Button>
    </div>
  )
}

export function SignOutButton() {
  const router = useRouter()
  const [busy, setBusy] = useState(false)
  return (
    <Button
      variant="ghost"
      size="sm"
      disabled={busy}
      onClick={async () => {
        setBusy(true)
        await attempt(() => browserApi.POST('/v1/auth/signout'))
        router.push('/')
        router.refresh()
      }}
    >
      Sign out
    </Button>
  )
}
