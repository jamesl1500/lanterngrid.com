'use client'

import { Alert, Button, cn } from '@lanterngrid/ui'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import {
  moveRow,
  sectionLabels,
  sectionRows,
  shownSections,
  type ProfileSection,
} from '@/lib/profile'

const hints: Record<ProfileSection, string> = {
  readme: 'Your README, when you have one.',
  pinned: 'Up to six snippets and repos.',
  friends: 'A few of your friends.',
  posts: 'Everything you post that the viewer can see.',
}

/** Choose which profile sections show, and in what order. */
export function SectionsForm({ initial }: { initial: ProfileSection[] }) {
  const router = useRouter()
  const [rows, setRows] = useState(() => sectionRows(initial))
  const [saved, setSaved] = useState(initial.join())
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)
  const sections = shownSections(rows)

  async function save(event: React.FormEvent) {
    event.preventDefault()
    setBusy(true)
    setStatus(null)
    const result = await attempt(() => browserApi.PATCH('/v1/me/profile', { body: { sections } }))
    setBusy(false)
    if (!result.ok) return setStatus({ tone: 'error', text: result.problem.message })
    setSaved(sections.join())
    setStatus({ tone: 'success', text: 'Profile layout saved.' })
    router.refresh()
  }

  const iconButton =
    'grid size-8 place-items-center border-2 border-line-strong bg-surface font-mono text-sm hover:bg-sunk disabled:opacity-30 disabled:hover:bg-surface'

  return (
    <form onSubmit={save} className="grid gap-3">
      {status ? <Alert tone={status.tone}>{status.text}</Alert> : null}
      <ol aria-label="Profile sections" className="border-2 border-line-strong">
        {rows.map((row, index) => {
          const label = sectionLabels[row.section]
          return (
            <li
              key={row.section}
              className={cn(
                'flex items-center gap-3 border-b border-line px-3 py-2.5 last:border-b-0',
                row.shown ? 'bg-surface' : 'bg-sunk',
              )}
            >
              <input
                id={`section-${row.section}`}
                type="checkbox"
                checked={row.shown}
                onChange={() =>
                  setRows((current) =>
                    current.map((r) => (r.section === row.section ? { ...r, shown: !r.shown } : r)),
                  )
                }
                className="size-4 accent-cyan"
              />
              <label htmlFor={`section-${row.section}`} className="grid min-w-0 flex-1">
                <span className={cn('font-semibold', !row.shown && 'text-ink-3 line-through')}>
                  {label}
                </span>
                <span className="text-sm text-ink-3">{hints[row.section]}</span>
              </label>
              <button
                type="button"
                aria-label={`Move ${label} up`}
                disabled={index === 0}
                onClick={() => setRows((current) => moveRow(current, index, -1))}
                className={iconButton}
              >
                ↑
              </button>
              <button
                type="button"
                aria-label={`Move ${label} down`}
                disabled={index === rows.length - 1}
                onClick={() => setRows((current) => moveRow(current, index, 1))}
                className={iconButton}
              >
                ↓
              </button>
            </li>
          )
        })}
      </ol>
      <div className="flex items-center justify-between gap-4">
        <span className="font-mono text-xs text-ink-3">
          {sections.length === 0 ? 'everything hidden' : `${sections.length} shown`}
        </span>
        <Button type="submit" disabled={busy || sections.join() === saved}>
          {busy ? 'Saving…' : 'Save layout'}
        </Button>
      </div>
    </form>
  )
}
