import type { Metadata } from 'next'

import { PostList } from '@/components/post-list'
import { serverApi } from '@/lib/api'
import { getMe, sessionToken } from '@/lib/session'

export const metadata: Metadata = { title: 'Explore' }

type Props = { searchParams: Promise<{ cursor?: string }> }

/** Every public post, newest first. Open to signed-out visitors too. */
export default async function ExplorePage({ searchParams }: Props) {
  const { cursor } = await searchParams
  const me = await getMe()
  const { data } = await serverApi(await sessionToken()).GET('/v1/explore', {
    params: { query: { cursor, limit: 20 } },
    cache: 'no-store',
  })
  if (!data) throw new Error('Could not load posts.')

  return (
    <main className="mx-auto grid max-w-2xl grid-cols-1 gap-6 px-4 py-8">
      <header className="grid gap-1">
        <span className="label">everyone</span>
        <h1 className="text-3xl font-bold">Explore</h1>
        <p className="text-ink-2">Public posts from across Lantern Grid, newest first.</p>
      </header>
      <PostList
        page={data}
        viewerId={me?.id}
        olderHref={(next) => `/explore?cursor=${next}`}
        empty={
          <>
            <span className="label">nothing yet</span>
            <p className="max-w-[40ch] text-ink-2">Public posts will show up here.</p>
          </>
        }
      />
    </main>
  )
}
