'use client'

import { Alert, Button, cn } from '@lanterngrid/ui'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import { MAX_README_LENGTH } from '@/lib/profile'

import { MarkdownPreview } from './markdown-preview'

/** Write the Markdown README that heads your profile, with a preview. */
export function ReadmeForm({ initial }: { initial: string | null }) {
  const router = useRouter()
  const [source, setSource] = useState(initial ?? '')
  const [saved, setSaved] = useState(initial ?? '')
  const [tab, setTab] = useState<'write' | 'preview'>('write')
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)
  const tooLong = source.length > MAX_README_LENGTH

  async function save(event: React.FormEvent) {
    event.preventDefault()
    setBusy(true)
    setStatus(null)
    const result = await attempt(() =>
      browserApi.PATCH('/v1/me/profile', { body: { readme_md: source } }),
    )
    setBusy(false)
    if (!result.ok) return setStatus({ tone: 'error', text: result.problem.message })
    setSaved(source)
    setStatus({ tone: 'success', text: source.trim() ? 'README saved.' : 'README removed.' })
    router.refresh()
  }

  const tabClass = (t: typeof tab) =>
    cn(
      'border-b-4 px-3 py-1.5 font-mono text-xs tracking-[0.08em] uppercase',
      tab === t ? 'border-cyan text-ink' : 'border-transparent text-ink-3 hover:text-ink',
    )

  return (
    <form onSubmit={save} className="grid gap-3">
      {status ? <Alert tone={status.tone}>{status.text}</Alert> : null}
      <div className="border-2 border-line-strong bg-sunk">
        <div role="tablist" aria-label="README" className="flex border-b border-line px-2 pt-1">
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'write'}
            className={tabClass('write')}
            onClick={() => setTab('write')}
          >
            Write
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === 'preview'}
            className={tabClass('preview')}
            onClick={() => setTab('preview')}
          >
            Preview
          </button>
          <span className="ml-auto self-center font-mono text-xs text-ink-3">README.md</span>
        </div>
        {tab === 'write' ? (
          <>
            <label htmlFor="readme" className="sr-only">
              README
            </label>
            <textarea
              id="readme"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              rows={12}
              aria-invalid={tooLong || undefined}
              placeholder={
                "## Hi, I'm …\n\nWhat you work on, what you're learning, how to reach you. Markdown and ```code blocks``` work."
              }
              className="block min-h-60 w-full resize-y bg-transparent px-4 py-3 font-mono text-sm placeholder:text-ink-3 focus:outline-none"
            />
          </>
        ) : (
          <div className="min-h-60 px-4 py-3">
            {source.trim() ? (
              <MarkdownPreview source={source} plain />
            ) : (
              <p className="text-ink-3">Nothing to preview yet.</p>
            )}
          </div>
        )}
      </div>
      <div className="flex items-center justify-between gap-4">
        <span className={cn('font-mono text-xs', tooLong ? 'text-coral' : 'text-ink-3')}>
          {source.length.toLocaleString('en')} / {MAX_README_LENGTH.toLocaleString('en')}
        </span>
        <Button type="submit" disabled={busy || tooLong || source === saved}>
          {busy ? 'Saving…' : 'Save README'}
        </Button>
      </div>
    </form>
  )
}
