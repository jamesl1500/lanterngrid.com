import { Button } from '@lanterngrid/ui'
import Link from 'next/link'

import { Composer } from '@/components/composer'
import { PostList } from '@/components/post-list'
import { serverApi } from '@/lib/api'
import { sessionToken, type Me } from '@/lib/session'

type Props = { me: Me & { username: string }; cursor?: string }

/** The signed-in home page: a composer, then your posts and your friends', newest first. */
export async function Feed({ me, cursor }: Props) {
  const { data } = await serverApi(await sessionToken()).GET('/v1/feed', {
    params: { query: { cursor, limit: 20 } },
    cache: 'no-store',
  })
  if (!data) throw new Error('Could not load your feed.')

  return (
    <main className="mx-auto grid max-w-2xl grid-cols-1 gap-6 px-4 py-8">
      <h1 className="sr-only">Your feed</h1>
      {cursor ? null : <Composer me={me} />}
      <PostList
        page={data}
        viewerId={me.id}
        olderHref={(next) => `/?cursor=${next}`}
        empty={
          <>
            <span className="label">your feed is empty</span>
            <p className="max-w-[44ch] text-ink-2">
              Posts from you and your friends show up here. Write something above, find people on
              the explore page or add a few friends.
            </p>
            <div className="flex flex-wrap justify-center gap-2 pt-2">
              <Button asChild variant="secondary" size="sm">
                <Link href="/explore">Explore</Link>
              </Button>
              <Button asChild variant="secondary" size="sm">
                <Link href="/friends">Find friends</Link>
              </Button>
            </div>
          </>
        }
      />
    </main>
  )
}
