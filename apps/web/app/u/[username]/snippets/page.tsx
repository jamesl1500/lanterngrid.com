import { Button, Card } from '@lanterngrid/ui'
import type { Metadata, Route } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

import { SnippetCard } from '@/components/snippet-card'
import { serverApi } from '@/lib/api'
import { getMe, sessionToken } from '@/lib/session'

type Props = {
  params: Promise<{ username: string }>
  searchParams: Promise<{ cursor?: string }>
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return { title: `Snippets by @${(await params).username}` }
}

export default async function UserSnippetsPage({ params, searchParams }: Props) {
  const [{ username }, { cursor }, me] = await Promise.all([params, searchParams, getMe()])
  const { data } = await serverApi(await sessionToken()).GET('/v1/users/{username}/snippets', {
    params: { path: { username }, query: { cursor, limit: 20 } },
    cache: 'no-store',
  })
  if (!data) notFound()
  const isMe = me?.username?.toLowerCase() === username.toLowerCase()

  return (
    <main className="mx-auto grid max-w-3xl grid-cols-1 gap-6 px-4 py-8">
      <header className="flex flex-wrap items-end justify-between gap-3 border-b-2 border-line-strong pb-3">
        <div className="grid gap-1">
          <Link
            href={`/u/${username}` as Route}
            className="font-mono text-xs text-ink-2 hover:text-ink"
          >
            ← @{username}
          </Link>
          <h1 className="text-3xl font-bold">Snippets</h1>
        </div>
        {isMe ? (
          <Button asChild variant="accent" size="sm">
            <Link href="/snippets/new">New snippet</Link>
          </Button>
        ) : null}
      </header>
      {data.items.length === 0 ? (
        <Card className="grid place-items-center gap-2 px-6 py-12 text-center">
          <span className="label">no snippets yet</span>
          <p className="max-w-[40ch] text-ink-2">
            {isMe
              ? 'Save a query, a config or a trick you keep looking up.'
              : `@${username} hasn't shared any snippets you can see.`}
          </p>
        </Card>
      ) : (
        <ol className="grid grid-cols-1 gap-4">
          {data.items.map((snippet) => (
            <li key={snippet.id}>
              <SnippetCard snippet={snippet} />
            </li>
          ))}
        </ol>
      )}
      {data.next_cursor ? (
        <Button asChild variant="secondary" className="justify-self-center">
          <Link href={`/u/${username}/snippets?cursor=${data.next_cursor}` as Route}>
            Older snippets
          </Link>
        </Button>
      ) : null}
    </main>
  )
}
