import { Button, Card } from '@lanterngrid/ui'
import type { Metadata, Route } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

import { PersonRow } from '@/components/person-row'
import { serverApi } from '@/lib/api'
import { sessionToken } from '@/lib/session'

type Props = {
  params: Promise<{ username: string }>
  searchParams: Promise<{ cursor?: string }>
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  return { title: `Friends of @${(await params).username}` }
}

export default async function FriendsOfPage({ params, searchParams }: Props) {
  const { username } = await params
  const { cursor } = await searchParams
  const api = serverApi(await sessionToken())
  const [profile, friends] = await Promise.all([
    api.GET('/v1/users/{username}', { params: { path: { username } }, cache: 'no-store' }),
    api.GET('/v1/users/{username}/friends', {
      params: { path: { username }, query: { cursor, limit: 30 } },
      cache: 'no-store',
    }),
  ])
  if (!profile.data || !friends.data) notFound()
  const person = profile.data

  return (
    <main className="mx-auto grid max-w-2xl gap-6 px-4 py-10">
      <header className="grid gap-1">
        <Link
          href={`/u/${person.username}` as Route}
          className="font-mono text-sm text-ink-3 hover:text-ink"
        >
          ← @{person.username}
        </Link>
        <h1 className="text-3xl font-bold">{person.display_name}&apos;s friends</h1>
        <p className="font-mono text-sm text-ink-3">
          {person.friend_count} {person.friend_count === 1 ? 'friend' : 'friends'}
        </p>
      </header>
      <Card className="px-4">
        {friends.data.items.length ? (
          <ul>
            {friends.data.items.map((friend) => (
              <PersonRow key={friend.id} person={friend} />
            ))}
          </ul>
        ) : (
          <p className="px-4 py-10 text-center text-ink-2">No friends to show yet.</p>
        )}
      </Card>
      {friends.data.next_cursor ? (
        <Button asChild variant="secondary" className="justify-self-center">
          <Link href={`/u/${person.username}/friends?cursor=${friends.data.next_cursor}` as Route}>
            More
          </Link>
        </Button>
      ) : null}
    </main>
  )
}
