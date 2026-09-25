import { Card, cn } from '@lanterngrid/ui'
import type { Metadata, Route } from 'next'
import Link from 'next/link'
import type { ReactNode } from 'react'

import { PeopleSearch } from '@/components/people-search'
import { PersonRow } from '@/components/person-row'
import { RequestActions } from '@/components/request-actions'
import { serverApi } from '@/lib/api'
import { requireMe, sessionToken } from '@/lib/session'

export const metadata: Metadata = { title: 'Friends' }

const tabs = ['friends', 'requests', 'sent'] as const
type Tab = (typeof tabs)[number]

function Empty({ children }: { children: ReactNode }) {
  return <p className="px-4 py-10 text-center text-ink-2">{children}</p>
}

export default async function FriendsPage({
  searchParams,
}: {
  searchParams: Promise<{ tab?: string }>
}) {
  const me = await requireMe('/friends')
  const requested = (await searchParams).tab
  const tab: Tab = tabs.includes(requested as Tab) ? (requested as Tab) : 'friends'
  const api = serverApi(await sessionToken())

  const [friends, incoming, outgoing] = await Promise.all([
    api.GET('/v1/users/{username}/friends', {
      params: { path: { username: me.username }, query: { limit: 50 } },
      cache: 'no-store',
    }),
    api.GET('/v1/me/friend-requests', {
      params: { query: { direction: 'incoming', limit: 50 } },
      cache: 'no-store',
    }),
    api.GET('/v1/me/friend-requests', {
      params: { query: { direction: 'outgoing', limit: 50 } },
      cache: 'no-store',
    }),
  ])
  if (!friends.data || !incoming.data || !outgoing.data) throw new Error('Could not load friends.')

  // Lists show up to 50; "50+" when there are more.
  const count = (page: { items: unknown[]; next_cursor: string | null }) =>
    page.items.length ? `${page.items.length}${page.next_cursor ? '+' : ''}` : null
  const counts: Record<Tab, string | null> = {
    friends: count(friends.data),
    requests: count(incoming.data),
    sent: count(outgoing.data),
  }
  const labels: Record<Tab, string> = { friends: 'Friends', requests: 'Requests', sent: 'Sent' }

  return (
    <main className="mx-auto grid max-w-2xl gap-6 px-4 py-10">
      <header className="grid gap-4">
        <h1 className="text-3xl font-bold">Friends</h1>
        <PeopleSearch />
      </header>

      <nav
        aria-label="Friends lists"
        className="flex border-b-2 border-line-strong font-mono text-sm"
      >
        {tabs.map((t) => (
          <Link
            key={t}
            href={(t === 'friends' ? '/friends' : `/friends?tab=${t}`) as Route}
            aria-current={t === tab ? 'page' : undefined}
            className={cn(
              '-mb-0.5 flex items-center gap-2 border-b-4 px-4 py-2',
              t === tab ? 'border-cyan text-ink' : 'border-transparent text-ink-2 hover:text-ink',
            )}
          >
            {labels[t]}
            {counts[t] ? (
              <span
                className={cn(
                  'px-1 text-xs',
                  t === 'requests' ? 'bg-coral font-bold text-[#0c1017]' : 'bg-sunk text-ink-2',
                )}
              >
                {counts[t]}
              </span>
            ) : null}
          </Link>
        ))}
      </nav>

      <Card className="px-4">
        {tab === 'friends' ? (
          friends.data.items.length ? (
            <ul>
              {friends.data.items.map((person) => (
                <PersonRow key={person.id} person={person} />
              ))}
            </ul>
          ) : (
            <Empty>No friends yet. Search for people you know and send a request.</Empty>
          )
        ) : tab === 'requests' ? (
          incoming.data.items.length ? (
            <ul>
              {incoming.data.items.map((request) => (
                <PersonRow key={request.id} person={request.user}>
                  <RequestActions requestId={request.id} actions={['accept', 'decline']} />
                </PersonRow>
              ))}
            </ul>
          ) : (
            <Empty>No requests waiting on you.</Empty>
          )
        ) : outgoing.data.items.length ? (
          <ul>
            {outgoing.data.items.map((request) => (
              <PersonRow key={request.id} person={request.user}>
                <RequestActions requestId={request.id} actions={['cancel']} />
              </PersonRow>
            ))}
          </ul>
        ) : (
          <Empty>You haven&apos;t sent any requests that are still waiting.</Empty>
        )}
      </Card>
    </main>
  )
}
