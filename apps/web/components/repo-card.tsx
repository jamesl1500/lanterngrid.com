import { accentClasses, Avatar, Card, cn, type Accent } from '@lanterngrid/ui'
import type { Route } from 'next'
import Link from 'next/link'
import type { ReactNode } from 'react'

import { formatCount, languageAccent, type Repo } from '@/lib/repos'
import { timeAgo } from '@/lib/time'

type Props = {
  repo: Repo
  showOwner?: boolean
  /** Owner controls, under the stats. */
  children?: ReactNode
}

/** A GitHub repo on a profile, a pin or a post: name, description and live stats. */
export function RepoCard({ repo, showOwner = false, children }: Props) {
  const [owner, name] = repo.full_name.split('/')
  const homepage = repo.homepage?.replace(/^https?:\/\//, '').replace(/\/$/, '')
  return (
    <Card className="grid grid-cols-1 border-l-4 border-l-lime">
      <div className="grid gap-2 px-4 py-3">
        <div className="flex items-start justify-between gap-3">
          <a
            href={repo.url}
            target="_blank"
            rel="noopener"
            className="min-w-0 font-mono text-sm break-words hover:underline"
          >
            <span className="text-ink-2">{owner}/</span>
            <span className="font-semibold text-ink">{name}</span>
          </a>
          <span className="flex shrink-0 gap-1.5">
            {repo.fork ? <Flag>fork</Flag> : null}
            {repo.archived ? <Flag>archived</Flag> : null}
          </span>
        </div>
        {repo.missing ? (
          <p className="text-sm text-coral">GitHub can&apos;t find this repo any more.</p>
        ) : null}
        {repo.description ? <p className="text-sm text-ink-2">{repo.description}</p> : null}
        {repo.topics.length > 0 ? (
          <ul aria-label="Topics" className="flex flex-wrap gap-1.5">
            {repo.topics.slice(0, 6).map((topic) => (
              <li
                key={topic}
                className="border border-lime bg-lime-soft px-1.5 font-mono text-[0.7rem] text-lime"
              >
                {topic}
              </li>
            ))}
          </ul>
        ) : null}
        <dl className="flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-xs text-ink-2">
          {repo.language ? (
            <div className="flex items-center gap-1.5">
              <dt className="sr-only">Language</dt>
              <span
                aria-hidden
                className={cn('size-2.5', accentClasses[languageAccent(repo.language)].solid)}
              />
              <dd>{repo.language}</dd>
            </div>
          ) : null}
          <Stat label="Stars" icon="★" value={repo.stars} />
          <Stat label="Forks" icon="⑂" value={repo.forks} />
          {repo.pushed_at ? (
            <div className="flex gap-1 text-ink-3">
              <dt>updated</dt>
              <dd>
                <time dateTime={repo.pushed_at}>{timeAgo(repo.pushed_at)}</time>
              </dd>
            </div>
          ) : null}
          {homepage ? (
            <div className="min-w-0">
              <dt className="sr-only">Website</dt>
              <dd className="truncate">
                <a
                  href={repo.homepage ?? undefined}
                  target="_blank"
                  rel="nofollow noopener"
                  className="text-lime hover:underline"
                >
                  {homepage}
                </a>
              </dd>
            </div>
          ) : null}
        </dl>
        {showOwner ? (
          <Link
            href={`/u/${repo.owner.username}/repos` as Route}
            className="flex items-center gap-1.5 font-mono text-xs text-ink-3 hover:text-ink"
          >
            <Avatar
              name={repo.owner.display_name}
              src={repo.owner.avatar_url}
              accent={repo.owner.accent_color as Accent}
              size="sm"
              className="size-5 text-[0.55rem]"
            />
            added by @{repo.owner.username}
          </Link>
        ) : null}
        {children}
      </div>
    </Card>
  )
}

function Stat({ label, icon, value }: { label: string; icon: string; value: number }) {
  return (
    <div className="flex items-center gap-1">
      <dt>
        <span aria-hidden>{icon}</span>
        <span className="sr-only">{label}</span>
      </dt>
      <dd>{formatCount(value)}</dd>
    </div>
  )
}

function Flag({ children }: { children: ReactNode }) {
  return (
    <span className="border border-line-strong px-1.5 font-mono text-[0.65rem] tracking-[0.08em] text-ink-3 uppercase">
      {children}
    </span>
  )
}
