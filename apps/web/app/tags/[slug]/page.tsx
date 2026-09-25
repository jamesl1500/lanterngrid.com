import { KindBadge } from '@lanterngrid/ui'
import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { cache } from 'react'

import { PostList } from '@/components/post-list'
import { serverApi } from '@/lib/api'
import { getMe, sessionToken } from '@/lib/session'

const getTag = cache(async (slug: string) => {
  const { data } = await serverApi().GET('/v1/tags/{slug}', {
    params: { path: { slug } },
    cache: 'no-store',
  })
  return data ?? null
})

type Props = {
  params: Promise<{ slug: string }>
  searchParams: Promise<{ cursor?: string }>
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const tag = await getTag(decodeURIComponent((await params).slug))
  return { title: tag ? `#${tag.name}` : 'Not found' }
}

/** Posts tagged with one tag that the viewer can see. */
export default async function TagPage({ params, searchParams }: Props) {
  const slug = decodeURIComponent((await params).slug)
  const [tag, { cursor }, me] = await Promise.all([getTag(slug), searchParams, getMe()])
  if (!tag) notFound()
  const { data } = await serverApi(await sessionToken()).GET('/v1/tags/{slug}/posts', {
    params: { path: { slug }, query: { cursor, limit: 20 } },
    cache: 'no-store',
  })
  if (!data) throw new Error('Could not load posts.')

  return (
    <main className="mx-auto grid max-w-2xl grid-cols-1 gap-6 px-4 py-8">
      <header className="grid gap-1 border-b-2 border-line-strong pb-4">
        <span className="label">{tag.kind}</span>
        <h1 className="font-mono text-3xl font-bold break-all">
          <span className="text-cyan">#</span>
          {tag.name}
        </h1>
      </header>
      <PostList
        page={data}
        viewerId={me?.id}
        olderHref={(next) => `/tags/${encodeURIComponent(slug)}?cursor=${next}`}
        empty={
          <>
            <KindBadge kind="update" />
            <p className="max-w-[40ch] text-ink-2">No posts you can see use this tag yet.</p>
          </>
        }
      />
    </main>
  )
}
