'use client'

import { Button } from '@lanterngrid/ui'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'

export function UnblockButton({ username }: { username: string }) {
  const router = useRouter()
  const [busy, setBusy] = useState(false)
  return (
    <Button
      size="sm"
      variant="secondary"
      disabled={busy}
      onClick={async () => {
        setBusy(true)
        await attempt(() =>
          browserApi.DELETE('/v1/me/blocks/{username}', { params: { path: { username } } }),
        )
        setBusy(false)
        router.refresh()
      }}
    >
      Unblock
    </Button>
  )
}
