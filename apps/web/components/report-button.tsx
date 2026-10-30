'use client'

import { Alert, Button, cn, Dialog } from '@lanterngrid/ui'
import { useRef, useState, type MouseEvent } from 'react'

import { browserApi } from '@/lib/api'
import { attempt } from '@/lib/errors'
import {
  MAX_REPORT_DETAILS,
  reasons,
  subjectName,
  type ReportReason,
  type SubjectKind,
} from '@/lib/moderation'

type Props = {
  kind: SubjectKind
  subjectId: string
  /** For people: their username, to name them. */
  username?: string
  /** How the trigger looks: a menu row, small text beside other actions, or a button. */
  look?: 'menu' | 'text' | 'button'
  className?: string
}

const looks = {
  menu: 'w-full px-3 py-2 text-left font-mono text-sm text-ink-2 hover:bg-sunk hover:text-ink',
  text: 'font-mono text-xs text-ink-3 hover:text-ink hover:underline',
  button: '',
}

/** "Report" plus the dialog that sends the report to moderators. */
export function ReportButton({ kind, subjectId, username, look = 'menu', className }: Props) {
  const [open, setOpen] = useState(false)
  const [reason, setReason] = useState<ReportReason | null>(null)
  const [details, setDetails] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sent, setSent] = useState(false)
  // The menu the button sits in, to close along with the dialog.
  const menu = useRef<HTMLDetailsElement | null>(null)
  const name = subjectName(kind, username)
  const needsDetails = reason === 'other' && !details.trim()

  function close() {
    setOpen(false)
    setReason(null)
    setDetails('')
    setError(null)
    setSent(false)
    menu.current?.removeAttribute('open')
  }

  function show(event: MouseEvent<HTMLElement>) {
    menu.current = event.currentTarget.closest('details')
    setOpen(true)
  }

  async function send(event: React.FormEvent) {
    event.preventDefault()
    if (!reason || needsDetails) return
    setBusy(true)
    setError(null)
    const result = await attempt(() =>
      browserApi.POST('/v1/reports', {
        body: {
          subject_kind: kind,
          subject_id: subjectId,
          reason,
          details: details.trim() || null,
        },
      }),
    )
    setBusy(false)
    if (!result.ok) return setError(result.problem.message)
    setSent(true)
  }

  const label = kind === 'user' ? `Report ${name}` : `Report ${kind}`
  return (
    <>
      {look === 'button' ? (
        <Button type="button" size="sm" variant="ghost" className={className} onClick={show}>
          <span className="text-coral">{label}</span>
        </Button>
      ) : (
        <button type="button" className={cn(looks[look], className)} onClick={show}>
          {look === 'text' ? 'report' : label}
        </button>
      )}
      <Dialog open={open} onClose={close} title={`Report ${name}`} accent="coral">
        {sent ? (
          <>
            <Alert tone="success">
              Thanks. A moderator will take a look and decide what to do.
            </Alert>
            <div className="flex justify-end">
              <Button type="button" size="sm" onClick={close}>
                Done
              </Button>
            </div>
          </>
        ) : (
          <form onSubmit={send} className="grid gap-4">
            <fieldset className="grid gap-1">
              <legend className="mb-2 text-sm text-ink-2">What&apos;s wrong with it?</legend>
              {reasons.map((r) => (
                <label
                  key={r.value}
                  className={cn(
                    'flex cursor-pointer items-start gap-3 border-2 px-3 py-2',
                    reason === r.value
                      ? 'border-coral bg-coral-soft'
                      : 'border-transparent hover:bg-sunk',
                  )}
                >
                  <input
                    type="radio"
                    name="report-reason"
                    value={r.value}
                    checked={reason === r.value}
                    onChange={() => setReason(r.value)}
                    className="mt-1 size-4 accent-coral"
                  />
                  <span className="grid">
                    <span className="font-semibold">{r.label}</span>
                    <span className="text-sm text-ink-3">{r.hint}</span>
                  </span>
                </label>
              ))}
            </fieldset>
            <div className="grid gap-1.5">
              <label htmlFor="report-details" className="text-sm text-ink-2">
                Anything moderators should know?{' '}
                <span className="text-ink-3">{reason === 'other' ? '(needed)' : '(optional)'}</span>
              </label>
              <textarea
                id="report-details"
                rows={3}
                maxLength={MAX_REPORT_DETAILS}
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                className="w-full resize-y border-2 border-line-strong bg-sunk px-3 py-2 placeholder:text-ink-3 focus:border-coral focus:outline-none"
              />
            </div>
            <p className="text-sm text-ink-3">
              {kind === 'message'
                ? 'Moderators will see this message. '
                : 'Moderators see what you report. '}
              {kind === 'user'
                ? "They aren't told who reported them."
                : "The author isn't told who reported it."}
            </p>
            {error ? <Alert tone="error">{error}</Alert> : null}
            <div className="flex justify-end gap-2">
              <Button type="button" size="sm" variant="ghost" onClick={close}>
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={busy || !reason || needsDetails}
                className="bg-coral text-[#0c1017]"
              >
                {busy ? 'Sending…' : 'Send report'}
              </Button>
            </div>
          </form>
        )}
      </Dialog>
    </>
  )
}
