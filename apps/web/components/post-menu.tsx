'use client'

import type { Route } from 'next'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'

const item = 'px-3 py-2 text-left font-mono text-sm hover:bg-sunk'

/** Edit and delete for your own posts. */
export function PostMenu({ postId, afterDelete }: { postId: string; afterDelete?: Route }) {
  const router = useRouter()
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)

  async function remove() {
    setBusy(true)
    const result = await attempt(() =>
      browserApi.DELETE('/v1/posts/{post_id}', { params: { path: { post_id: postId } } }),
    )
    setBusy(false)
    if (!result.ok) return
    if (afterDelete) router.push(afterDelete)
    router.refresh()
  }

  return (
    <details className="relative">
      <summary
        aria-label="Post actions"
        className="flex h-7 cursor-pointer list-none items-center px-1.5 font-mono text-sm text-ink-3 select-none hover:bg-sunk hover:text-ink [&::-webkit-details-marker]:hidden"
      >
        •••
      </summary>
      <div className="absolute right-0 z-20 mt-1 grid w-44 border-2 border-line-strong bg-surface shadow-hard">
        <button
          type="button"
          className={item}
          onClick={() => router.push(`/p/${postId}/edit` as Route)}
        >
          Edit
        </button>
        {confirming ? (
          <button
            type="button"
            disabled={busy}
            onClick={remove}
            className={`${item} bg-coral-soft text-coral`}
          >
            {busy ? 'Deleting…' : 'Yes, delete it'}
          </button>
        ) : (
          <button
            type="button"
            className={`${item} text-coral`}
            onClick={() => setConfirming(true)}
          >
            Delete
          </button>
        )}
      </div>
    </details>
  )
}
