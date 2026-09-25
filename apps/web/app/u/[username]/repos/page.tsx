import { Button, Card } from '@lanterngrid/ui'
import type { Metadata, Route } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

import { AddRepoForm } from '@/components/add-repo-form'
import { RepoActions } from '@/components/repo-actions'
import { RepoCard } from '@/components/repo-card'
import { serverApi } from '@/lib/api'
import { getMe, sessionToken } from '@/lib/session'

type Props = {
  params: Promise<{ username: string }>
  searchParams: Promise<{ cursor?: string }>
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return { title: `Repos by @${(await params).username}` }
}

export default async function UserReposPage({ params, searchParams }: Props) {
  const [{ username }, { cursor }, me] = await Promise.all([params, searchParams, getMe()])
  const api = serverApi(await sessionToken())
  const path = { username }
  const [{ data }, { data: pins }] = await Promise.all([
    api.GET('/v1/users/{username}/repos', {
      params: { path, query: { cursor, limit: 20 } },
      cache: 'no-store',
    }),
    api.GET('/v1/users/{username}/pins', { params: { path }, cache: 'no-store' }),
  ])
  if (!data) notFound()
  const isMe = me?.username?.toLowerCase() === username.toLowerCase()
  const pinned = new Set(pins?.items.flatMap((p) => (p.repo ? [p.repo.id] : [])))

  return (
    <main className="mx-auto grid max-w-3xl grid-cols-1 gap-6 px-4 py-8">
      <header className="grid gap-1 border-b-2 border-line-strong pb-3">
        <Link
          href={`/u/${username}` as Route}
          className="font-mono text-xs text-ink-2 hover:text-ink"
        >
          ← @{username}
        </Link>
        <h1 className="text-3xl font-bold">Repos</h1>
      </header>
      {isMe ? <AddRepoForm /> : null}
      {data.items.length === 0 ? (
        <Card className="grid place-items-center gap-2 px-6 py-12 text-center">
          <span className="label">no repos yet</span>
          <p className="max-w-[40ch] text-ink-2">
            {isMe
              ? 'Add the projects you want people to see. Stars and forks stay up to date.'
              : `@${username} hasn't added any repos yet.`}
          </p>
        </Card>
      ) : (
        <ol className="grid grid-cols-1 gap-4">
          {data.items.map((repo) => (
            <li key={repo.id}>
              <RepoCard repo={repo}>
                {isMe ? (
                  <RepoActions
                    repoId={repo.id}
                    fullName={repo.full_name}
                    pinned={pinned.has(repo.id)}
                  />
                ) : null}
              </RepoCard>
            </li>
          ))}
        </ol>
      )}
      {data.next_cursor ? (
        <Button asChild variant="secondary" className="justify-self-center">
          <Link href={`/u/${username}/repos?cursor=${data.next_cursor}` as Route}>Older repos</Link>
        </Button>
      ) : null}
    </main>
  )
}
