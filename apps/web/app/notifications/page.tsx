import type { Schemas } from '@lanterngrid/api-client'
import { Avatar, Button, Card, cn, type Accent } from '@lanterngrid/ui'
import type { Metadata, Route } from 'next'
import Link from 'next/link'

import { MarkNotificationsRead } from '@/components/mark-notifications-read'
import { serverApi } from '@/lib/api'
import { requireMe, sessionToken } from '@/lib/session'
import { timeAgo } from '@/lib/time'

export const metadata: Metadata = { title: 'Notifications' }

type Note = Schemas['NotificationOut']

function describe(note: Note): { text: string; href: Route } {
  switch (note.kind) {
    case 'friend_request':
      return { text: 'sent you a friend request.', href: '/friends?tab=requests' as Route }
    case 'friend_accepted':
      return {
        text: 'accepted your friend request.',
        href: `/u/${note.actor.username}` as Route,
      }
    case 'mention':
      return {
        text: 'mentioned you in a post.',
        href: (note.subject_id ? `/p/${note.subject_id}` : '/') as Route,
      }
  }
}

export default async function NotificationsPage({
  searchParams,
}: {
  searchParams: Promise<{ cursor?: string }>
}) {
  await requireMe('/notifications')
  const { cursor } = await searchParams
  const { data } = await serverApi(await sessionToken()).GET('/v1/me/notifications', {
    params: { query: { cursor, limit: 30 } },
    cache: 'no-store',
  })
  if (!data) throw new Error('Could not load notifications.')
  const newestUnread = data.items.find((n) => !n.read)?.id ?? null

  return (
    <main className="mx-auto grid max-w-2xl gap-6 px-4 py-10">
      <MarkNotificationsRead upTo={newestUnread} />
      <h1 className="text-3xl font-bold">Notifications</h1>
      {data.items.length === 0 ? (
        <Card className="grid place-items-center gap-2 px-6 py-12 text-center">
          <span className="label">all quiet</span>
          <p className="max-w-[40ch] text-ink-2">Friend requests and mentions will show up here.</p>
        </Card>
      ) : (
        <Card>
          <ol>
            {data.items.map((note) => {
              const { text, href } = describe(note)
              return (
                <li
                  key={note.id}
                  className={cn(
                    'border-b border-line border-l-4 last:border-b-0',
                    note.read ? 'border-l-transparent' : 'border-l-coral bg-coral-soft/40',
                  )}
                >
                  <Link href={href} className="flex items-center gap-3 px-4 py-3 hover:bg-sunk">
                    <Avatar
                      name={note.actor.display_name}
                      src={note.actor.avatar_url}
                      accent={note.actor.accent_color as Accent}
                      size="md"
                    />
                    <span className="min-w-0 flex-1">
                      <span className="font-semibold">{note.actor.display_name}</span> {text}
                    </span>
                    <time
                      dateTime={note.created_at}
                      className="shrink-0 font-mono text-xs text-ink-3"
                    >
                      {timeAgo(note.created_at)}
                    </time>
                    {note.read ? null : <span className="sr-only">(new)</span>}
                  </Link>
                </li>
              )
            })}
          </ol>
        </Card>
      )}
      {data.next_cursor ? (
        <Button asChild variant="secondary" className="justify-self-center">
          <Link href={`/notifications?cursor=${data.next_cursor}` as Route}>Older</Link>
        </Button>
      ) : null}
    </main>
  )
}
