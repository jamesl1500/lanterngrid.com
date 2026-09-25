'use client'

import { Alert, Button, cn } from '@lanterngrid/ui'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import { MAX_COMMENT_LENGTH } from '@/lib/posts'

import { AutocompleteTextarea } from './autocomplete-textarea'

/** Add a comment to a post. @people autocomplete. */
export function CommentForm({ postId }: { postId: string }) {
  const router = useRouter()
  const [body, setBody] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const remaining = MAX_COMMENT_LENGTH - body.length

  async function submit() {
    if (!body.trim() || remaining < 0 || busy) return
    setBusy(true)
    setError(null)
    const result = await attempt(() =>
      browserApi.POST('/v1/posts/{post_id}/comments', {
        params: { path: { post_id: postId } },
        body: { body_md: body },
      }),
    )
    setBusy(false)
    if (!result.ok) {
      setError(Object.values(result.problem.fields)[0] ?? result.problem.message)
      return
    }
    setBody('')
    router.refresh()
  }

  return (
    <div className="border-2 border-line-strong bg-surface">
      <AutocompleteTextarea
        label="Write a comment"
        value={body}
        onChange={setBody}
        onSubmit={() => void submit()}
        triggers={['@']}
        rows={2}
        placeholder="Add a comment. Markdown and @people work."
        className="min-h-16"
      />
      {error ? (
        <Alert tone="error" className="mx-4 mb-3">
          {error}
        </Alert>
      ) : null}
      <div className="flex items-center justify-end gap-3 border-t border-line px-4 py-2">
        {remaining < 200 ? (
          <span className={cn('font-mono text-xs', remaining < 0 ? 'text-coral' : 'text-amber')}>
            {remaining}
          </span>
        ) : null}
        <Button
          type="button"
          size="sm"
          variant="accent"
          disabled={busy || !body.trim() || remaining < 0}
          onClick={() => void submit()}
        >
          {busy ? 'Sending…' : 'Comment'}
        </Button>
      </div>
    </div>
  )
}
