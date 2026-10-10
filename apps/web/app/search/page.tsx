import { Card, cn } from '@lanterngrid/ui'
import type { Metadata, Route } from 'next'
import Link from 'next/link'

import { PersonRow } from '@/components/person-row'
import { PostList } from '@/components/post-list'
import { SearchBox } from '@/components/search-box'
import { serverApi } from '@/lib/api'
import { getMe, sessionToken } from '@/lib/session'

type Props = { searchParams: Promise<{ q?: string; tab?: string; cursor?: string }> }

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const q = (await searchParams).q?.trim()
  return { title: q ? `“${q}”: search` : 'Search' }
}

const tabs = ['posts', 'people'] as const
type Tab = (typeof tabs)[number]

/** Posts by full-text search, and people by name (people need an account). */
export default async function SearchPage({ searchParams }: Props) {
  const params = await searchParams
  const q = (params.q ?? '').trim().slice(0, 200)
  const tab: Tab = params.tab === 'people' ? 'people' : 'posts'
  const me = await getMe()
  const api = serverApi(await sessionToken())
  const href = (t: Tab) => `/search?${new URLSearchParams({ q, tab: t })}` as Route

  const posts =
    q && tab === 'posts'
      ? (
          await api.GET('/v1/search/posts', {
            params: { query: { q, cursor: params.cursor, limit: 20 } },
            cache: 'no-store',
          })
        ).data
      : undefined
  const people =
    q && tab === 'people' && me?.username
      ? (
          await api.GET('/v1/people/search', {
            params: { query: { q: q.slice(0, 50), limit: 20 } },
            cache: 'no-store',
          })
        ).data
      : undefined

  return (
    <main className="mx-auto grid max-w-2xl grid-cols-1 gap-6 px-4 py-8">
      <header className="grid gap-4">
        <h1 className="text-3xl font-bold">Search</h1>
        <SearchBox defaultValue={q} tab={tab} autoFocus={!q} />
        <nav aria-label="Search for" className="flex border-b-2 border-line-strong">
          {tabs.map((t) => (
            <Link
              key={t}
              href={href(t)}
              aria-current={t === tab ? 'page' : undefined}
              className={cn(
                '-mb-0.5 border-b-4 px-4 py-2 font-mono text-sm capitalize',
                t === tab ? 'border-cyan text-ink' : 'border-transparent text-ink-3 hover:text-ink',
              )}
            >
              {t}
            </Link>
          ))}
        </nav>
      </header>

      {!q ? (
        <p className="text-ink-2">
          {tab === 'posts'
            ? 'Search every post you can see. Use "quotes" for a phrase and -word to leave a word out.'
            : 'Find people by username or name.'}
        </p>
      ) : tab === 'posts' ? (
        posts ? (
          <PostList
            page={posts}
            viewerId={me?.id}
            olderHref={(next) => `/search?${new URLSearchParams({ q, tab, cursor: next })}`}
            empty={
              <>
                <span className="label">no matches</span>
                <p className="max-w-[40ch] text-ink-2">
                  No posts you can see match “{q}”. Try fewer or different words.
                </p>
              </>
            }
          />
        ) : (
          <p className="text-coral">Search isn&apos;t working right now. Try again in a bit.</p>
        )
      ) : !me?.username ? (
        <p className="text-ink-2">
          <Link
            href={`/signin?next=${encodeURIComponent(href('people'))}` as Route}
            className="text-cyan hover:underline"
          >
            Sign in
          </Link>{' '}
          to search for people.
        </p>
      ) : people && people.length > 0 ? (
        <Card className="px-4">
          <ul>
            {people.map((person) => (
              <PersonRow key={person.id} person={person} />
            ))}
          </ul>
        </Card>
      ) : (
        <Card className="grid place-items-center gap-2 px-6 py-12 text-center">
          <span className="label">no one found</span>
          <p className="text-ink-2">No one goes by “{q}”.</p>
        </Card>
      )}
    </main>
  )
}
