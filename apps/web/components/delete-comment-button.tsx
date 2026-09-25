'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'

const button = 'font-mono text-xs hover:underline disabled:opacity-60'

/** Delete a comment, after a second click to confirm. */
export function DeleteCommentButton({ commentId }: { commentId: string }) {
  const router = useRouter()
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)

  async function remove() {
    setBusy(true)
    const result = await attempt(() =>
      browserApi.DELETE('/v1/comments/{comment_id}', {
        params: { path: { comment_id: commentId } },
      }),
    )
    setBusy(false)
    if (result.ok) router.refresh()
  }

  if (!confirming) {
    return (
      <button type="button" className={`${button} text-ink-3`} onClick={() => setConfirming(true)}>
        delete
      </button>
    )
  }
  return (
    <span className="flex gap-2">
      <button type="button" disabled={busy} className={`${button} text-coral`} onClick={remove}>
        {busy ? 'deleting…' : 'yes, delete'}
      </button>
      <button type="button" className={`${button} text-ink-3`} onClick={() => setConfirming(false)}>
        keep
      </button>
    </span>
  )
}
