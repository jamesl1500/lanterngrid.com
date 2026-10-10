import { Avatar, Card, cn, type Accent } from '@lanterngrid/ui'
import type { Metadata, Route } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

import { CaseActions, LiftSuspensionButton } from '@/components/case-actions'
import { serverApi } from '@/lib/api'
import {
  reasonLabel,
  reasonSummary,
  statusLabel,
  subjectHref,
  type ModerationCase,
  type SubjectKind,
} from '@/lib/moderation'
import { requireMe, sessionToken } from '@/lib/session'
import { timeAgo } from '@/lib/time'

export const metadata: Metadata = { title: 'Moderation' }

type Props = { searchParams: Promise<{ tab?: string; cursor?: string }> }

const tabs = ['open', 'closed'] as const
type Tab = (typeof tabs)[number]

// Each kind takes its content accent; people get coral, the alert color.
const kindStyle: Record<SubjectKind, string> = {
  post: 'border-cyan bg-cyan-soft text-cyan',
  comment: 'border-cyan bg-cyan-soft text-cyan',
  snippet: 'border-violet bg-violet-soft text-violet',
  message: 'border-magenta bg-magenta-soft text-magenta',
  user: 'border-coral bg-coral-soft text-coral',
}

/** The report queue: open cases to decide, and closed ones for the record. */
export default async function ModerationPage({ searchParams }: Props) {
  const me = await requireMe('/mod')
  if (!me.is_moderator) notFound()
  const params = await searchParams
  const tab: Tab = params.tab === 'closed' ? 'closed' : 'open'
  const api = serverApi(await sessionToken())
  const [page, summary] = await Promise.all([
    api.GET('/v1/moderation/cases', {
      params: { query: { status: tab, cursor: params.cursor, limit: 20 } },
      cache: 'no-store',
    }),
    api.GET('/v1/moderation/summary', { cache: 'no-store' }),
  ])
  if (!page.data) throw new Error('Could not load the moderation queue.')
  const open = summary.data?.open_cases ?? 0

  return (
    <main className="mx-auto grid max-w-3xl grid-cols-1 gap-6 px-4 py-8">
      <header className="grid gap-4">
        <div className="grid gap-1">
          <span className="label text-coral">moderation</span>
          <h1 className="text-3xl font-bold">Reports</h1>
        </div>
        <nav aria-label="Cases" className="flex border-b-2 border-line-strong">
          {tabs.map((t) => (
            <Link
              key={t}
              href={(t === 'open' ? '/mod' : '/mod?tab=closed') as Route}
              aria-current={t === tab ? 'page' : undefined}
              className={cn(
                '-mb-0.5 border-b-4 px-4 py-2 font-mono text-sm capitalize',
                t === tab
                  ? 'border-coral text-ink'
                  : 'border-transparent text-ink-3 hover:text-ink',
              )}
            >
              {t}
              {t === 'open' && open > 0 ? <span className="ml-2 text-coral">{open}</span> : null}
            </Link>
          ))}
        </nav>
      </header>

      {page.data.items.length === 0 ? (
        <Card className="grid place-items-center gap-2 px-6 py-12 text-center">
          <span className="label">{tab === 'open' ? 'all clear' : 'nothing yet'}</span>
          <p className="text-ink-2">
            {tab === 'open'
              ? 'No open reports. New ones show up here.'
              : 'Decided reports are kept here.'}
          </p>
        </Card>
      ) : (
        <ol className="grid grid-cols-1 gap-4">
          {page.data.items.map((c) => (
            <li key={c.id}>
              <CaseCard found={c} />
            </li>
          ))}
        </ol>
      )}

      {page.data.next_cursor ? (
        <Link
          href={`/mod?${new URLSearchParams({ tab, cursor: page.data.next_cursor })}` as Route}
          className="justify-self-center font-mono text-sm text-ink-2 hover:text-ink"
        >
          Older →
        </Link>
      ) : null}
    </main>
  )
}

function CaseCard({ found: c }: { found: ModerationCase }) {
  const author = c.subject_author
  const href = subjectHref(c)
  const isOpen = c.status === 'open'
  return (
    <Card className={cn('grid gap-3 border-l-4 p-4', isOpen ? 'border-l-coral' : 'border-l-line')}>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <span
          className={cn(
            'border px-1.5 py-px font-mono text-[0.68rem] tracking-[0.08em] uppercase',
            kindStyle[c.subject_kind],
          )}
        >
          {c.subject_kind === 'user' ? 'person' : c.subject_kind}
        </span>
        {author ? (
          <Link
            href={`/u/${author.username}` as Route}
            className="flex min-w-0 items-center gap-2 text-sm hover:underline"
          >
            <Avatar
              name={author.display_name}
              src={author.avatar_url}
              accent={author.accent_color as Accent}
              size="sm"
            />
            <span className="truncate font-semibold">{author.display_name}</span>
            <span className="font-mono text-xs text-ink-3">@{author.username}</span>
          </Link>
        ) : (
          <span className="text-sm text-ink-3">Deleted account</span>
        )}
        {c.author_suspended ? (
          <span className="border border-coral px-1.5 font-mono text-xs text-coral">suspended</span>
        ) : null}
        <span className="ml-auto font-mono text-xs text-ink-3">
          {c.report_count} {c.report_count === 1 ? 'report' : 'reports'} ·{' '}
          <time dateTime={c.created_at}>{timeAgo(c.created_at)}</time>
        </span>
      </div>

      <p className="text-sm font-semibold text-coral">{reasonSummary(c.reports)}</p>

      <div
        className={cn(
          'max-h-72 overflow-auto border border-line bg-sunk px-3 py-2 break-words whitespace-pre-wrap',
          c.subject_kind === 'snippet' && 'font-mono text-sm',
        )}
      >
        {c.snapshot}
      </div>
      <p className="flex flex-wrap gap-x-1.5 font-mono text-xs text-ink-3">
        <span>as first reported ·</span>
        {c.subject_gone ? (
          <span>since deleted</span>
        ) : c.author_suspended ? (
          <span>hidden while the author is suspended</span>
        ) : href ? (
          <Link href={href as Route} className="text-ink-2 hover:text-ink hover:underline">
            see it in place →
          </Link>
        ) : (
          <span>private message</span>
        )}
      </p>

      <details className="group">
        <summary className="cursor-pointer font-mono text-xs text-ink-2 select-none hover:text-ink">
          who reported it
        </summary>
        <ul className="mt-2 grid gap-2">
          {c.reports.map((r) => (
            <li key={r.id} className="border-l-2 border-line pl-3 text-sm">
              <span className="font-mono text-xs text-ink-3">
                @{r.reporter.username} · {reasonLabel[r.reason]} ·{' '}
                <time dateTime={r.created_at}>{timeAgo(r.created_at)}</time>
              </span>
              {r.details ? <p className="whitespace-pre-wrap text-ink-2">{r.details}</p> : null}
            </li>
          ))}
        </ul>
      </details>

      {isOpen ? (
        <CaseActions found={c} />
      ) : (
        <div className="grid gap-2 border-t border-line pt-3">
          <p className="text-sm">
            <span className="font-semibold">{statusLabel[c.status]}</span>
            <span className="text-ink-3">
              {c.resolved_by ? ` by @${c.resolved_by.username}` : ''}
              {c.resolved_at ? ` · ${timeAgo(c.resolved_at)}` : ''}
            </span>
          </p>
          {c.note ? <p className="text-sm text-ink-2">“{c.note}”</p> : null}
          {c.status === 'suspended' && c.author_suspended && author ? (
            <LiftSuspensionButton userId={author.id} username={author.username} />
          ) : null}
        </div>
      )}
    </Card>
  )
}
