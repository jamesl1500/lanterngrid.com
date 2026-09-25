'use client'

import { Alert, Button } from '@lanterngrid/ui'
import { useRouter } from 'next/navigation'
import { useState, type FormEvent } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'

/** Paste a GitHub link or owner/name to add a public repo to your profile. */
export function AddRepoForm() {
  const router = useRouter()
  const [value, setValue] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!value.trim() || busy) return
    setBusy(true)
    setError(null)
    const result = await attempt(() => browserApi.POST('/v1/repos', { body: { repo: value } }))
    setBusy(false)
    if (!result.ok) {
      setError(Object.values(result.problem.fields)[0] ?? result.problem.message)
      return
    }
    setValue('')
    router.refresh()
  }

  return (
    <form onSubmit={submit} className="grid gap-2 border-2 border-line-strong bg-surface p-3">
      <label
        htmlFor="add-repo"
        className="font-mono text-xs tracking-[0.08em] text-ink-2 uppercase"
      >
        Add a GitHub repo
      </label>
      <div className="flex gap-2">
        <input
          id="add-repo"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="github.com/you/project or you/project"
          autoComplete="off"
          spellCheck={false}
          className="h-9 min-w-0 flex-1 border-2 border-line-strong bg-sunk px-3 font-mono text-sm placeholder:text-ink-3 focus:border-lime focus:outline-none"
        />
        <Button
          type="submit"
          size="sm"
          variant="accent"
          disabled={busy || !value.trim()}
          className="h-9"
        >
          {busy ? 'Adding…' : 'Add'}
        </Button>
      </div>
      {error ? <Alert tone="error">{error}</Alert> : null}
    </form>
  )
}
